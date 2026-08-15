# Design Document: Backend Parser Integration

## Overview

This document describes the integration layer that connects ForenSync's existing parser plugins to the Flask backend. The goal is to take a file that has already been saved by the upload route, detect which parser plugin handles it, invoke the parser, map the resulting normalized events to `TimelineEvent` database rows, and update the `LogFile` job status throughout.

Nothing in `Backend/parsers/` or `Backend/models/__init__.py` is modified. The integration is entirely new code in `Backend/services/parser_service.py` and modifications to `Backend/routes/upload.py`.

### Flow Summary

```
POST /api/v1/upload (multipart: file + optional caseId)
        │
        ▼
  Upload Route
  ├─ Validates file (extension, filename safety)
  ├─ Saves file to UPLOAD_FOLDER as {JOB_ID}_{secure_filename}
  ├─ Creates LogFile row (parse_status = "queued"), commits
  └─ Calls ParserService.process_upload(filepath, job_id, case_id, log_file_id)
              │
              ▼
        Parser Service
        ├─ detect_parser(filename) → source_name
        ├─ get_plugin(source_name) → plugin instance
        ├─ Updates LogFile.parse_status = "processing", commits
        ├─ plugin.parse(filepath) → List[Dict]  (Normalized_Events)
        ├─ Maps each dict → TimelineEvent row
        ├─ Bulk inserts TimelineEvent rows, commits
        ├─ Updates LogFile.parse_status = "parsed", commits
        └─ Returns event_count
              │
              ▼
  Upload Route
  └─ Returns HTTP 200 { jobId, parseStatus, eventCount, ... }
```

---

## Architecture

The integration follows the existing service-layer pattern already established by `auth_service.py`: the route handles HTTP concerns (parsing the request, forming the response, catching typed exceptions) while the service handles business logic (detection, invocation, persistence). The two layers communicate through a clean function boundary and a small set of custom exceptions.

```
┌───────────────────────┐
│  routes/upload.py     │  ← HTTP layer: request/response, exception → HTTP status
│  (Upload_Route)       │
└──────────┬────────────┘
           │  calls process_upload()
           ▼
┌───────────────────────┐
│ services/             │  ← Business logic: detection, invocation, persistence
│  parser_service.py    │
│  (Parser_Service)     │
└──────────┬────────────┘
           │  sys.path manipulation → imports
           ▼
┌───────────────────────┐
│ parsers/plugins/      │  ← Untouched existing code
│  registry.py          │
│  auth_log.py          │
│  linux_syslog.py      │
│  apache_access.py     │
│  nginx_access.py      │
│  windows_event_log.py │
└───────────────────────┘
           │  reads / returns
           ▼
┌───────────────────────┐
│ models/__init__.py    │  ← Untouched existing SQLAlchemy models
│  LogFile              │
│  TimelineEvent        │
└───────────────────────┘
```

### Key Design Decisions

**Synchronous processing**: Parsing runs synchronously inside the request-response cycle. This keeps the implementation simple and avoids needing a task queue (Celery, RQ, etc.). For large files this means a slower response, but it's appropriate for the current forensic investigation use case where investigators expect to wait for results.

**sys.path manipulation at module import time**: The plugins use relative imports (`from plugins.base import BaseParserPlugin`). The Flask app runs from `Backend/`, so `Backend/parsers/` must be on `sys.path`. This is done once at the top of `parser_service.py`, not inside any function, so it's applied the moment the module is first imported.

**Atomic status transitions as separate commits**: Each status change (`queued → processing → parsed/failed`) is committed immediately rather than batching with the event inserts. This means the database always reflects the true current state even if a later step crashes mid-flight.

**Custom exception hierarchy**: Three typed exceptions (`UnsupportedFileError`, `ParserExecutionError`, `DatabasePersistenceError`) let the route map each failure mode to the correct HTTP status code without inspecting exception messages.

---

## Components and Interfaces

### Upload Route (`Backend/routes/upload.py`)

The existing route is extended, not replaced. The path `POST /api/v1/upload` is unchanged.

**New responsibilities after the existing save-and-record logic:**

```python
from services.parser_service import (
    process_upload,
    UnsupportedFileError,
    ParserExecutionError,
    DatabasePersistenceError,
)

# After LogFile is committed:
try:
    event_count = process_upload(
        filepath=save_path,
        job_id=job_id,
        case_id=case_id,
        log_file_id=log_file.id,
    )
except UnsupportedFileError as e:
    return error_response(str(e), 422, error="Unsupported File")
except ParserExecutionError as e:
    return error_response(str(e), 500, error="Parser Error")
except DatabasePersistenceError as e:
    return error_response(str(e), 500, error="Database Error")

return success_response(
    data={
        "filename":    uploaded.filename,
        "size":        file_size,
        "caseId":      case_id,
        "jobId":       job_id,
        "parseStatus": "parsed",
        "eventCount":  event_count,
    },
    message="File parsed successfully.",
)
```

### Parser Service (`Backend/services/parser_service.py`)

**Public API:**

| Symbol | Signature | Description |
|---|---|---|
| `detect_parser` | `(filename: str) -> str` | Returns the `source_name` string for a given filename. Independently testable. |
| `process_upload` | `(filepath, job_id, case_id, log_file_id) -> int` | Full orchestration. Returns event count on success, raises on failure. |
| `UnsupportedFileError` | `Exception` subclass | Raised when no plugin matches the file. |
| `ParserExecutionError` | `Exception` subclass | Raised when `plugin.parse()` raises. |
| `DatabasePersistenceError` | `Exception` subclass | Raised when the DB commit for events fails. |

**Internal helpers (private):**

- `_map_severity(result: str, action: str) -> str` — applies the severity rules from Requirement 5.
- `_map_event(event: dict, case_id: str, log_file_id: int) -> TimelineEvent` — converts one Normalized_Event dict to a `TimelineEvent` ORM object.

### Plugin Registry (unchanged)

`Backend/parsers/plugins/registry.py` exposes:
- `get_plugin(source_name, **kwargs)` — instantiates and returns a plugin.
- `list_available_plugins()` — returns registered names.

The `Parser_Service` calls `get_plugin()` only. If the name is not found, the registry raises `ValueError`; the service catches this and re-raises as `UnsupportedFileError`.

---

## Data Models

### Normalized_Event (plugin output dict)

All plugins produce dicts conforming to `BaseParserPlugin._build_event()`:

| Key | Type | Example |
|---|---|---|
| `timestamp` | `str` ISO-8601 UTC | `"2005-06-18T02:08:11Z"` |
| `source` | `str` | `"auth_log"` |
| `host` | `str` | `"LabSZ"` |
| `actor` | `str` | `"192.168.1.1"` |
| `action` | `str` | `"ssh_login_failed"` |
| `object` | `str` | `"root"` |
| `result` | `str` | `"failure"` |
| `raw_log` | `str` | original log line |

### TimelineEvent (SQLAlchemy model — unchanged)

| Column | Source |
|---|---|
| `case_id` | passed from route via `process_upload` |
| `log_file_id` | `LogFile.id` passed from route |
| `timestamp` | `datetime` parsed from event `timestamp` string; falls back to `utcnow()` if string is `"unknown"` |
| `timestamp_str` | raw `timestamp` string from event dict |
| `source` | event `source` |
| `event_type` | event `action` |
| `severity` | computed by `_map_severity(result, action)` |
| `description` | `f"{actor} performed {action} on {object}"` |
| `raw_log` | event `raw_log` |

### LogFile (SQLAlchemy model — unchanged)

The service reads and writes only `parse_status` and `id`. No other columns are touched by the service.

### Parse Status State Machine

```
         Upload Route
              │
         [file saved]
              │
              ▼
         ┌─────────┐
         │ queued  │  ← LogFile created here, committed by Upload Route
         └────┬────┘
              │  process_upload() called
              ▼
         ┌────────────┐
         │ processing │  ← committed before plugin.parse() is called
         └─────┬──────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌────────┐    ┌────────┐
   │ parsed │    │ failed │  ← each committed immediately before re-raise
   └────────┘    └────────┘
```

State transitions are always committed before the next potentially-failing operation so the database is never left in a stale state.

---

## File Type Detection

`detect_parser(filename)` applies rules to the lowercased filename and extension in priority order:

```
Extension .evtx                           → "windows_event_log"
Extension .log, name contains "auth"      → "auth_log"
Extension .log, name contains "syslog"
                 or "linux"               → "linux_syslog"
Extension .log, name contains "apache"
                 or "access"              → "apache_access"
Extension .log, name contains "nginx"     → "nginx_access"
Extension .log  (no keyword match)        → "linux_syslog"  (default)
Anything else                             → raises UnsupportedFileError
```

The `.txt` extension is not currently mapped to any parser. Files with `.txt` extension pass the upload validator (it's in `ALLOWED_EXTENSIONS`) but `detect_parser` will raise `UnsupportedFileError`, which the route maps to HTTP 422. This is intentional — if `.txt` support is needed in the future, a rule can be added to `detect_parser` without touching anything else.

### sys.path Manipulation

At the top of `parser_service.py`, before any plugin imports:

```python
import sys
import os

_PARSERS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "parsers")
)
if _PARSERS_DIR not in sys.path:
    sys.path.insert(0, _PARSERS_DIR)

from plugins.registry import get_plugin, list_available_plugins
```

This runs once at module import time. The `if` guard prevents duplicate entries if the module is somehow reimported. The path resolves to `Backend/parsers/` regardless of the working directory.

---

## Severity Mapping

`_map_severity(result: str, action: str) -> str` evaluates rules in order and returns the first match:

| Priority | Condition | Severity |
|---|---|---|
| 1 | `result == "failure"` AND (`"login"` in `action` OR `"ssh"` in `action`) | `"Critical"` |
| 2 | `result == "failure"` | `"Warning"` |
| 3 | `action in {"root_console_login", "windows_privileged_logon"}` | `"Warning"` |
| 4 | _(default)_ | `"Info"` |

Examples:
- `action="ssh_login_failed", result="failure"` → **Critical** (rule 1)
- `action="ftp_connection", result="unknown"` → **Info** (rule 4)
- `action="root_console_login", result="success"` → **Warning** (rule 3)
- `action="windows_logon_success", result="success"` → **Info** (rule 4)

---

## Error Handling

### Custom Exception Classes

```python
class UnsupportedFileError(Exception):
    """Raised when no plugin is registered for the detected source name."""

class ParserExecutionError(Exception):
    """Raised when plugin.parse() raises any exception."""

class DatabasePersistenceError(Exception):
    """Raised when the DB commit for TimelineEvent rows fails."""
```

### Exception Flow in `process_upload`

```
detect_parser()
    ValueError from registry → re-raised as UnsupportedFileError

LogFile status = "processing" commit
    SQLAlchemy error → logged + raised as DatabasePersistenceError

plugin.parse(filepath)
    any Exception → logged (with traceback) + raised as ParserExecutionError
    on failure: status set to "failed", committed, then re-raise

_map_event() + db.session.add_all() + db.session.commit()
    SQLAlchemy error → rollback + status set to "failed", committed
                     → raised as DatabasePersistenceError

LogFile status = "parsed" commit
    SQLAlchemy error → logged (non-fatal if events already saved)
```

### Logging

All logging uses `current_app.logger` (not a module-level logger) so the Flask app's configured log level and format are respected:

| Event | Level |
|---|---|
| Parse start (file, source_name, job_id) | INFO |
| Parse result (event count) | INFO |
| Parser exception (with traceback) | ERROR |
| DB persistence failure (with traceback) | ERROR |
| Status transition | DEBUG |

---

## Testing Strategy

Tests live entirely in `Backend/tests/`. No file in `Backend/parsers/` is modified.

### Test Configuration

Tests use Flask's `TestingConfig` which sets `SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"` and `TESTING = True`. A `conftest.py` will create the app, initialize the in-memory database, and provide a test client fixture.

The `init_db()` function from `models/__init__.py` is called in the test fixture to create all tables. A minimal `Case` row (e.g. `CASE-TEST`) is seeded before upload tests that require a valid `case_id` foreign key.

### Unit Tests (specific examples and edge cases)

- `detect_parser("auth_log_sample.log")` returns `"auth_log"`
- `detect_parser("linux_syslog_sample.log")` returns `"linux_syslog"`
- `detect_parser("apache_access_sample.log")` returns `"apache_access"`
- `detect_parser("nginx_access_sample.log")` returns `"nginx_access"`
- `detect_parser("security.evtx")` returns `"windows_event_log"`
- `detect_parser("unknown_file.log")` returns `"linux_syslog"` (default)
- `_map_severity("failure", "ssh_login_failed")` returns `"Critical"`
- `_map_severity("failure", "ftp_connection")` returns `"Warning"`
- `_map_severity("success", "root_console_login")` returns `"Warning"`
- `_map_severity("success", "ssh_login_success")` returns `"Info"`
- Upload with `.exe` file → HTTP 415
- Upload with unsupported but allowed extension (`.txt`, no matching parser) → HTTP 422
- Upload when `parse()` raises `RuntimeError` → HTTP 500, `parse_status = "failed"` in DB
- Upload with valid `.log` file → HTTP 200, response contains `parseStatus` and `eventCount`
- `eventCount` in response equals number of `TimelineEvent` rows in DB for that `log_file_id`

### Property-Based Tests

Property-based tests use `hypothesis` (already in `Backend/requirements.txt` or to be added). Each property test runs a minimum of 100 iterations.

Each test is tagged with a comment in the format:
`# Feature: backend-parser-integration, Property N: <property text>`

### Sample Log Idempotence Tests

For each file in `Backend/parsers/sample_logs/` that has a matching parser, the test uploads it twice (in separate in-memory DB transactions) and asserts both runs produce the same event count. This validates Requirement 10.8.

### Dual Testing Approach Summary

Unit tests catch concrete bugs (wrong HTTP status code, wrong DB field value, specific severity mapping). Property tests verify universal invariants (all events are persisted, severity is always one of the valid values, detect_parser covers all extensions deterministically). Both are required for comprehensive coverage.

**Property-based testing library**: `hypothesis`
**Minimum iterations per property**: 100 (configured via `@settings(max_examples=100)`)

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: detect_parser is a total deterministic function over filenames

*For any* filename string, `detect_parser(filename)` returns exactly one of the five registered source names (`auth_log`, `linux_syslog`, `apache_access`, `nginx_access`, `windows_event_log`) or raises `UnsupportedFileError`, and calling it twice with the same input always returns the same output.

**Validates: Requirements 2.1, 2.4**

### Property 2: Event persistence completeness

*For any* file successfully processed by `process_upload`, the integer returned by `process_upload` (event count) equals the number of `TimelineEvent` rows in the database whose `log_file_id` matches the originating `LogFile.id`.

**Validates: Requirements 3.2, 4.1, 10.7**

### Property 3: Normalized_Event field mapping correctness

*For any* Normalized_Event dict produced by a parser plugin, the `TimelineEvent` row created by `_map_event` satisfies: `event.source == dict["source"]`, `event.event_type == dict["action"]`, `event.raw_log == dict["raw_log"]`, `event.timestamp_str == dict["timestamp"]`, and `event.description` contains the `actor`, `action`, and `object` values from the dict.

**Validates: Requirements 4.2**

### Property 4: Severity mapping is total and rule-ordered

*For any* `(result, action)` string pair, `_map_severity(result, action)` returns exactly one of `"Critical"`, `"Warning"`, or `"Info"`, and the result satisfies:
- `"failure"` in result AND (`"login"` or `"ssh"` in action) → `"Critical"`
- `"failure"` in result AND no login/ssh keyword → `"Warning"`
- action is `"root_console_login"` or `"windows_privileged_logon"` → `"Warning"`
- all other inputs → `"Info"`

**Validates: Requirements 5.1, 5.2**

### Property 5: Successful parse always sets parse_status to "parsed"

*For any* upload that completes without exception, `LogFile.parse_status` is `"parsed"` after `process_upload` returns.

**Validates: Requirements 6.2**

### Property 6: Any parse or persist failure sets parse_status to "failed"

*For any* upload where `plugin.parse()` or the database commit raises an exception, `LogFile.parse_status` is `"failed"` in the database after the exception propagates.

**Validates: Requirements 6.3**

### Property 7: Successful upload returns HTTP 200 with eventCount

*For any* valid file upload that parses without error, the HTTP response status is 200 and the `data` object in the response body contains an integer `eventCount` key and a `parseStatus` key.

**Validates: Requirements 7.2, 10.2**

### Property 8: Parse idempotence on sample log files

*For any* file in `Backend/parsers/sample_logs/` that has a matching parser, parsing the file twice (in independent runs against an empty database) produces the same number of events both times.

**Validates: Requirements 10.8**

---

## Error Handling

### Custom Exception Classes

All three exception classes are defined at the top of `parser_service.py` and inherit directly from `Exception`:

```python
class UnsupportedFileError(Exception):
    """Raised when detect_parser cannot find a matching plugin for the file."""

class ParserExecutionError(Exception):
    """Raised when plugin.parse() raises any exception during file processing."""

class DatabasePersistenceError(Exception):
    """Raised when the database commit for TimelineEvent rows fails."""
```

### Exception Handling in process_upload

```
┌─────────────────────────────────────────────────────────────────┐
│ process_upload(filepath, job_id, case_id, log_file_id)          │
│                                                                  │
│  detect_parser(filename)                                         │
│    └─ ValueError from registry → UnsupportedFileError           │
│                                                                  │
│  set status = "processing", commit                               │
│    └─ SQLAlchemyError → DatabasePersistenceError                 │
│                                                                  │
│  plugin.parse(filepath)                                          │
│    └─ any Exception → log traceback at ERROR                     │
│                      → set status = "failed", commit             │
│                      → raise ParserExecutionError(original msg)  │
│                                                                  │
│  build and insert TimelineEvent rows, commit                     │
│    └─ SQLAlchemyError → rollback                                 │
│                        → set status = "failed", commit           │
│                        → raise DatabasePersistenceError          │
│                                                                  │
│  set status = "parsed", commit                                   │
│  return event_count                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Exception Handling in the Upload Route

The route catches exceptions in specificity order — typed exceptions before the bare `Exception` fallback registered by the global error handler in `app.py`:

```python
except UnsupportedFileError as e:
    return error_response(str(e), 422, error="Unsupported File")
except ParserExecutionError as e:
    return error_response(str(e), 500, error="Parser Error")
except DatabasePersistenceError as e:
    return error_response(str(e), 500, error="Database Error")
```

### HTTP Status Code Mapping

| Exception | HTTP Status | error field |
|---|---|---|
| `UnsupportedFileError` | 422 | `"Unsupported File"` |
| `ParserExecutionError` | 500 | `"Parser Error"` |
| `DatabasePersistenceError` | 500 | `"Database Error"` |
| File extension not in `ALLOWED_EXTENSIONS` | 415 | `"Unsupported Media Type"` |
| Invalid/missing file in request | 400 | `"Bad Request"` |

---

## Testing Strategy

### Framework and Configuration

- **Test runner**: `pytest`
- **Property-based testing**: `hypothesis` with `@settings(max_examples=100)` minimum
- **Test location**: `Backend/tests/` — all test files live here
- **Database**: In-memory SQLite via `TestingConfig` (`SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"`)

### conftest.py Fixtures

```python
@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        init_db(app)   # creates tables
        # seed a test case for FK integrity
        case = Case(case_id="CASE-TEST", name="Test Case", org_id="ORG-4410", ...)
        db.session.add(case)
        db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()
```

### Dual Testing Approach

**Unit tests** (`test_upload_route.py`, `test_parser_service.py`) cover:
- Specific HTTP status codes for each error path
- `detect_parser` with concrete filenames for each parser keyword
- `_map_severity` with specific `(result, action)` pairs
- DB state after a failed parse (parse_status = "failed")
- eventCount in response equals TimelineEvent rows in DB

**Property-based tests** (`test_parser_service_properties.py`) cover:
- `detect_parser` over randomly generated filenames with seeded extensions/keywords
- `_map_severity` over all combinations of result and action strings
- Field mapping correctness over randomly generated Normalized_Event dicts
- Parse idempotence over all sample log files

### Property Test Tag Format

Each property-based test includes a comment in the format:
```python
# Feature: backend-parser-integration, Property N: <property text>
```

### Property Test Examples

```python
# Feature: backend-parser-integration, Property 4: Severity mapping is total and rule-ordered
@given(result=st.text(), action=st.text())
@settings(max_examples=100)
def test_severity_mapping_total(result, action):
    severity = _map_severity(result, action)
    assert severity in {"Critical", "Warning", "Info"}

# Feature: backend-parser-integration, Property 3: Normalized_Event field mapping correctness
@given(event=st.fixed_dictionaries({
    "timestamp": st.text(), "source": st.text(), "host": st.text(),
    "actor": st.text(), "action": st.text(), "object": st.text(),
    "result": st.text(), "raw_log": st.text(),
}))
@settings(max_examples=100)
def test_field_mapping(event, app):
    with app.app_context():
        te = _map_event(event, "CASE-TEST", 1)
        assert te.source == event["source"]
        assert te.event_type == event["action"]
        assert te.raw_log == event["raw_log"]
        assert te.timestamp_str == event["timestamp"]
```

### Sample Log Integration Tests

For each `.log` or `.evtx` file in `Backend/parsers/sample_logs/` that has a matching parser, a parametrized test uploads the file and asserts HTTP 200 with a non-negative `eventCount`. A second pass re-uploads the same file and asserts the same event count (Property 8).

### Test File Layout

```
Backend/tests/
├── __init__.py
├── conftest.py
├── test_upload_route.py         # HTTP-level integration tests
├── test_parser_service.py       # Unit tests for detect_parser, severity, mapping
└── test_parser_service_props.py # Hypothesis property-based tests
```
