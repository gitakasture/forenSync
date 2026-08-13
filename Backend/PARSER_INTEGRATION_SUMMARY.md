# Backend Parser Integration - Implementation Summary

## Overview

This integration connects ForenSync's existing parser plugins to the Flask backend, enabling uploaded log files from the React frontend to be automatically processed, normalized into timeline events, and persisted to the SQLite database.

## Architecture

```
React Frontend
  ↓ POST /api/v1/upload (multipart file + optional caseId)
  ↓
Upload Route (Backend/routes/upload.py)
  ↓ validates file, saves to disk, creates LogFile record
  ↓
Parser Service (Backend/services/parser_service.py)
  ↓ detects parser, invokes plugin.parse()
  ↓
Parser Plugin (Backend/parsers/plugins/*.py) [UNMODIFIED]
  ↓ returns normalized events
  ↓
Parser Service
  ↓ maps events to TimelineEvent rows, persists to database
  ↓
Database (SQLite via SQLAlchemy) [SCHEMA UNMODIFIED]
  ↓
Upload Route
  ↓ returns JSON response with eventCount
  ↓
React Frontend [UNMODIFIED]
```

## Files Created

### Backend/services/parser_service.py
**Purpose:** Core integration service orchestrating the parse flow

**Key Functions:**
- `process_upload(filepath, job_id, case_id, log_file_id) -> int`
  - Main orchestration function
  - Returns event count on success
  - Raises typed exceptions on failure

- `detect_parser(filename) -> str`
  - Maps filename/extension to parser source name
  - Priority rules: .evtx → windows_event_log, .log with keywords → specific parsers, fallback → linux_syslog

- `_map_event(event, case_id, log_file_id) -> TimelineEvent`
  - Converts normalized event dict to TimelineEvent ORM object
  - Maps fields: timestamp, source, action, severity, description, raw_log

- `_map_severity(result, action) -> str`
  - Applies severity rules: failure + login/ssh → Critical, other failures → Warning, privileged actions → Warning, default → Info

- `_update_parse_status(log_file_id, status)`
  - Atomic status transitions: queued → processing → parsed/failed

**Custom Exceptions:**
- `UnsupportedFileError` → HTTP 422
- `ParserExecutionError` → HTTP 500
- `DatabasePersistenceError` → HTTP 500

### Backend/tests/conftest.py
**Purpose:** Pytest configuration and fixtures

**Fixtures:**
- `app`: Flask application in testing mode with in-memory database
- `client`: Test client for HTTP requests
- Seeds test organization, user, and case for FK integrity

### Backend/tests/test_parser_service.py
**Purpose:** Unit tests for parser service functions

**Test Coverage:**
- `detect_parser()` with various filename patterns
- `_map_severity()` with different result/action combinations
- Parser selection correctness
- Unsupported file handling

### Backend/tests/test_upload_route.py
**Purpose:** HTTP integration tests for upload endpoint

**Test Coverage:**
- File upload with valid log files
- Parser integration and event count in response
- Unsupported file types (HTTP 415)
- Unsupported extensions with parsing (HTTP 422)
- Parse status transitions in database
- Event persistence in database
- Severity mapping correctness

### Backend/tests/test_parser_service_props.py
**Purpose:** Property-based tests using hypothesis

**Properties Tested:**
1. `detect_parser` is deterministic
2. `_map_severity` is total and returns valid values
3. Severity rules are correctly ordered
4. Filename extension detection coverage

## Files Modified

### Backend/routes/upload.py
**Changes:**
- Added import of `process_upload` and custom exceptions from `parser_service`
- Added parser integration after LogFile creation
- Catches typed exceptions and maps to appropriate HTTP status codes
- Returns `eventCount` and `parseStatus: "parsed"` in success response

### Backend/app.py
**Changes:**
- Added database initialization via `init_db(app)` on application startup
- Ensures SQLite database tables are created before any routes handle requests

### Backend/config.py
**Changes:**
- Updated `TestingConfig` to set `MAX_CONTENT_LENGTH = 100 MB` for testing with large sample log files

### Backend/requirements.txt
**Changes:**
- Added `Flask-SQLAlchemy==3.1.1` for SQLite ORM
- Added `pytest==8.3.5` for testing framework
- Added `hypothesis==6.130.1` for property-based testing

## Files Confirmed Unmodified

✅ **Backend/parsers/** - All parser plugin files remain unchanged
✅ **Backend/supabase_schema.sql** - Database schema unchanged
✅ **forensync-ui/** - React frontend unchanged

## Integration Flow

1. **Upload Request:**
   - Frontend POST to `/api/v1/upload` with file and optional caseId
   - Backend validates extension (ALLOWED_EXTENSIONS)
   - Saves file as `{JOB_ID}_{secure_filename}`

2. **Database Record:**
   - Creates LogFile row with `parse_status = "queued"`
   - Commits to database

3. **Parser Detection:**
   - `detect_parser(filename)` maps to source name
   - Gets plugin instance from existing registry

4. **Parse Execution:**
   - Updates LogFile `parse_status = "processing"`
   - Calls `plugin.parse(filepath)`
   - Receives list of normalized event dicts

5. **Event Persistence:**
   - Maps each event dict to TimelineEvent row
   - Applies severity mapping rules
   - Bulk inserts all events in single transaction
   - Updates LogFile `parse_status = "parsed"`

6. **Response:**
   - Returns HTTP 200 with `eventCount` and `parseStatus`
   - On error: HTTP 422 (unsupported), HTTP 500 (parser error, DB error)

## Parser Selection Rules

Priority order (first match wins):

1. `.evtx` → `windows_event_log`
2. `.log` + "nginx" → `nginx_access`
3. `.log` + "auth" → `auth_log`
4. `.log` + ("syslog" or "linux") → `linux_syslog`
5. `.log` + ("apache" or "access") → `apache_access`
6. `.log` (no keywords) → `linux_syslog` (default)
7. Other extensions → `UnsupportedFileError`

## Severity Mapping Rules

Priority order (first match wins):

1. `result == "failure"` AND (`"login"` OR `"ssh"` in action) → `Critical`
2. `result == "failure"` → `Warning`
3. `action` in `{"root_console_login", "windows_privileged_logon"}` → `Warning`
4. Default → `Info`

## Parse Status Lifecycle

```
queued (LogFile created by upload route)
  ↓
processing (before plugin.parse() call)
  ↓
parsed (success) OR failed (exception)
```

Each transition is committed immediately so database always reflects current state.

## API Contract (Unchanged)

**Request:**
```
POST /api/v1/upload
Content-Type: multipart/form-data

file: <binary log file>
caseId: CASE-1042 (optional, defaults to CASE-1042)
```

**Response (Success - Extended):**
```json
{
  "status": "success",
  "message": "File parsed successfully.",
  "data": {
    "filename": "auth_log_sample.log",
    "size": 123456,
    "caseId": "CASE-1042",
    "jobId": "JOB-AB12CD34",
    "parseStatus": "parsed",
    "eventCount": 42
  }
}
```

**Response (Error - Unsupported File):**
```json
{
  "status": "error",
  "error": "Unsupported File",
  "message": "No parser plugin registered for source 'unknown' (file: notes.txt)"
}
```

## Test Results

```
======================== 27 passed, 1 warning in 76.00s ========================

✅ 7 tests for detect_parser() - all parsers correctly identified
✅ 4 tests for _map_severity() - all severity rules work correctly
✅ 6 tests for property-based correctness - determinism, totality, coverage
✅ 10 tests for HTTP upload integration - all scenarios covered
```

### Test Coverage:
- Parser selection for all supported file types
- Severity mapping for all rule branches
- HTTP status codes for all error scenarios
- Database state verification after parse
- Event persistence completeness
- Parse status lifecycle
- Property-based invariants (100 iterations each)

## Commands to Run

### Install Dependencies:
```bash
cd Backend
pip install -r requirements.txt
```

### Run Tests:
```bash
cd Backend
python -m pytest tests/ -v
```

### Start Backend:
```bash
cd Backend
python run.py
```

### Test Upload (curl example):
```bash
curl -X POST http://localhost:5000/api/v1/upload \
  -F "file=@parsers/sample_logs/auth_log_sample.log" \
  -F "caseId=CASE-1042"
```

## Integration Limitations

### None Currently
All planned integration points are complete:
- ✅ Parser discovery and selection
- ✅ Parser invocation
- ✅ Event normalization and mapping
- ✅ Database persistence
- ✅ Parse status lifecycle
- ✅ Error handling and logging
- ✅ API contract preservation
- ✅ Comprehensive test coverage

## Future Enhancements (Not Required for This Integration)

1. **Asynchronous Processing:**
   - Move parsing to a background task queue (Celery/RQ) for large files
   - Return job ID immediately, poll for completion

2. **Parser Configuration:**
   - Allow users to specify starting year for auth_log/syslog parsers
   - Support custom parser plugin registration

3. **Event Filtering:**
   - Allow filtering events by severity before persistence
   - Support custom event transformation rules

4. **Performance Optimization:**
   - Batch insert optimization for very large log files
   - Streaming parser support for files > 100 MB

5. **Monitoring:**
   - Parse duration metrics
   - Event count distribution by severity
   - Parser success/failure rates

## Confirmation

✅ **Backend/parsers/** - UNMODIFIED
✅ **forensync-ui/** - UNMODIFIED  
✅ **Backend/supabase_schema.sql** - UNMODIFIED
✅ **Database schema** - NO CHANGES
✅ **API contract** - PRESERVED (extended with eventCount)
✅ **All tests passing** - 27/27
✅ **Parser integration** - COMPLETE
✅ **Error handling** - COMPLETE
✅ **Logging** - COMPLETE
