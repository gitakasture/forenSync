# Requirements Document

## Introduction

This feature connects ForenSync's existing parser plugins to the Flask backend so that log files uploaded from the React frontend are automatically processed, normalized into timeline events, and persisted to the SQLite database. The backend already has a working upload endpoint, a validated parser plugin library (`Backend/parsers/plugins/`), a plugin registry (`registry.py`), and a SQLAlchemy model layer (`models/__init__.py`). The work here is the integration layer only — no parsers, no frontend, and no database schema are modified.

The intended flow is:

```
React Frontend
  → POST /api/v1/upload (multipart file + optional caseId)
  → Upload Route validates and saves file to disk
  → Parser Integration Service selects correct parser from registry
  → Parser produces normalized events (List[Dict])
  → Events persisted as TimelineEvent rows in SQLite via SQLAlchemy
  → Success response returned to frontend with job ID and event count
```

---

## Glossary

- **Upload_Route**: The Flask view function at `POST /api/v1/upload` defined in `Backend/routes/upload.py`.
- **Parser_Service**: The new integration service to be created at `Backend/services/parser_service.py`. It orchestrates file type detection, parser selection, and event persistence.
- **Plugin_Registry**: The existing module at `Backend/parsers/plugins/registry.py`. Exposes `get_plugin(source_name)` and `list_available_plugins()`. Must not be modified.
- **Parser_Plugin**: Any class in `Backend/parsers/plugins/` that inherits from `BaseParserPlugin` and implements `parse(filepath) -> List[Dict]`. Must not be modified.
- **Normalized_Event**: A Python dict produced by a Parser_Plugin with keys: `timestamp`, `source`, `host`, `actor`, `action`, `object`, `result`, `raw_log`.
- **TimelineEvent**: The SQLAlchemy model in `Backend/models/__init__.py` that persists Normalized_Events. Must not be modified.
- **LogFile**: The SQLAlchemy model in `Backend/models/__init__.py` tracking file upload metadata and parse status. Must not be modified.
- **Job_ID**: A unique string identifier (e.g. `JOB-AB12CD34`) generated per upload, stored on the LogFile row, and returned to the frontend.
- **Parse_Status**: The current state of a LogFile job. Valid values: `queued`, `processing`, `parsed`, `failed`.
- **File_Type_Detector**: Logic within the Parser_Service that maps a file's extension and/or filename pattern to a Plugin_Registry source name (e.g. `.evtx` → `windows_event_log`).
- **UPLOAD_FOLDER**: The filesystem directory configured in `config.py` where uploaded files are saved, resolved to `Backend/uploads/` by default.

---

## Requirements

### Requirement 1: File Persistence on Upload

**User Story:** As an investigator, I want uploaded log files to be saved to disk and recorded in the database, so that they can be referenced and processed reliably.

#### Acceptance Criteria

1. WHEN a valid file is submitted to `POST /api/v1/upload`, THE Upload_Route SHALL save the file to UPLOAD_FOLDER using a collision-safe name in the format `{Job_ID}_{secure_filename}`.
2. WHEN a file is saved to disk, THE Upload_Route SHALL create a LogFile database record with fields: `filename` (original name), `stored_filename` (collision-safe name), `file_size` (bytes), `job_id`, `parse_status` set to `queued`, and `case_id` from the form field.
3. WHEN the LogFile record is created, THE Upload_Route SHALL commit the record to the database before triggering parsing.
4. IF the file cannot be saved to disk, THEN THE Upload_Route SHALL return an HTTP 500 error response and SHALL NOT create a LogFile record.

---

### Requirement 2: Parser Selection

**User Story:** As an investigator, I want the backend to automatically select the correct parser for my uploaded file, so that I don't have to manually configure the parsing step.

#### Acceptance Criteria

1. THE Parser_Service SHALL map file extensions to Plugin_Registry source names using the following rules:
   - `.log` files with names containing `auth` → `auth_log`
   - `.log` files with names containing `syslog` or `linux` → `linux_syslog`
   - `.log` files with names containing `apache` or `access` → `apache_access`
   - `.log` files with names containing `nginx` → `nginx_access`
   - `.evtx` files → `windows_event_log`
   - `.log` files with no matching name pattern → `linux_syslog` (default fallback)
2. WHEN a source name is determined, THE Parser_Service SHALL call `get_plugin(source_name)` from the Plugin_Registry to obtain an instantiated Parser_Plugin.
3. IF the resolved source name is not found in the Plugin_Registry, THEN THE Parser_Service SHALL raise a `UnsupportedFileError` with a message identifying the file and the source name attempted.
4. THE Parser_Service SHALL expose a `detect_parser(filename: str) -> str` function that returns the source name string for a given filename, to allow independent testability of the detection logic.

---

### Requirement 3: Parser Invocation

**User Story:** As an investigator, I want the parser to process my uploaded file and produce structured forensic events, so that the data can be added to the case timeline.

#### Acceptance Criteria

1. WHEN a Parser_Plugin is selected, THE Parser_Service SHALL call `plugin.parse(filepath)` with the absolute path to the saved file.
2. WHEN `parse()` returns successfully, THE Parser_Service SHALL return the full list of Normalized_Events to the caller.
3. IF `parse()` raises an exception, THEN THE Parser_Service SHALL catch it, log the error including the job ID and file path, and raise a `ParserExecutionError` wrapping the original exception message.
4. THE Parser_Service SHALL log the start of parsing (file path, source name, job ID) and the result (event count or error) at INFO level.

---

### Requirement 4: Event Persistence

**User Story:** As an investigator, I want parsed events to be stored in the database, so that the frontend can display a forensic timeline.

#### Acceptance Criteria

1. WHEN a list of Normalized_Events is returned by the Parser_Plugin, THE Parser_Service SHALL persist each event as a TimelineEvent row linked to the `case_id` and `log_file_id` of the originating LogFile.
2. THE Parser_Service SHALL map Normalized_Event fields to TimelineEvent columns as follows:
   - `timestamp` (ISO 8601 string from event) → `timestamp_str` and parsed `timestamp` (DateTime)
   - `source` → `source`
   - `action` → `event_type`
   - `result` + `action` → `severity` (see Requirement 5)
   - `actor` + `action` + `object` joined as a sentence → `description`
   - `raw_log` → `raw_log`
3. WHEN all TimelineEvent rows are created, THE Parser_Service SHALL commit them in a single database transaction.
4. IF the database commit fails, THEN THE Parser_Service SHALL roll back the transaction, log the error, and raise a `DatabasePersistenceError`.

---

### Requirement 5: Event Severity Mapping

**User Story:** As an investigator, I want events to be tagged with a severity level, so that I can quickly identify high-priority events in the timeline.

#### Acceptance Criteria

1. THE Parser_Service SHALL assign `severity` to each TimelineEvent using the following rules (evaluated in order):
   - IF `result` is `failure` AND `action` contains `login` or `ssh` → `Critical`
   - IF `result` is `failure` → `Warning`
   - IF `action` is `root_console_login` or `windows_privileged_logon` → `Warning`
   - Otherwise → `Info`
2. THE Parser_Service SHALL default to `Info` if none of the above conditions match.

---

### Requirement 6: Parse Status Lifecycle

**User Story:** As an investigator, I want to know whether my file was parsed successfully or if something went wrong, so that I can take corrective action.

#### Acceptance Criteria

1. WHEN parsing begins, THE Parser_Service SHALL update the LogFile `parse_status` to `processing` and commit before calling `parse()`.
2. WHEN parsing and persistence complete successfully, THE Parser_Service SHALL update the LogFile `parse_status` to `parsed` and commit.
3. IF parsing or persistence raises any exception, THEN THE Parser_Service SHALL update the LogFile `parse_status` to `failed` and commit, before re-raising the exception to the caller.
4. THE Parser_Service SHALL update `parse_status` atomically — each status transition SHALL be a separate database commit so that status is always current even if later steps fail.

---

### Requirement 7: Upload Endpoint Integration

**User Story:** As a frontend developer, I want the upload endpoint to return a consistent response with job status information, so that the frontend can display feedback to investigators without any changes.

#### Acceptance Criteria

1. WHEN the Upload_Route successfully saves a file and triggers parsing, THE Upload_Route SHALL call `Parser_Service.process_upload(filepath, job_id, case_id, log_file_id)` synchronously.
2. WHEN `process_upload` returns successfully, THE Upload_Route SHALL return HTTP 200 with the existing response shape, extended to include `eventCount` (integer) in the `data` object.
3. IF `process_upload` raises `UnsupportedFileError`, THEN THE Upload_Route SHALL return HTTP 422 with `error` = `"Unsupported File"` and a message identifying the unsupported file type.
4. IF `process_upload` raises `ParserExecutionError`, THEN THE Upload_Route SHALL return HTTP 500 with `error` = `"Parser Error"` and the error message from the exception.
5. IF `process_upload` raises `DatabasePersistenceError`, THEN THE Upload_Route SHALL return HTTP 500 with `error` = `"Database Error"` and the error message from the exception.
6. THE Upload_Route SHALL NOT be renamed or moved. The endpoint path `POST /api/v1/upload` SHALL remain unchanged.

---

### Requirement 8: Parser Module Import Path

**User Story:** As a backend developer, I want the Parser_Service to import parser plugins correctly regardless of working directory, so that integration works when the Flask app is started from `Backend/`.

#### Acceptance Criteria

1. THE Parser_Service SHALL add `Backend/parsers/` to `sys.path` before importing from the Plugin_Registry, so that `from plugins.registry import get_plugin` resolves correctly at runtime.
2. THE Parser_Service SHALL perform the `sys.path` manipulation once at module import time, not inside the function body.
3. WHEN the Flask app is started from `Backend/` using `python run.py`, THE Parser_Service SHALL successfully import the Plugin_Registry without a `ModuleNotFoundError`.

---

### Requirement 9: Error Handling and Logging

**User Story:** As a backend developer, I want all failure scenarios to be safely handled and logged, so that forensic data is never silently lost and issues are diagnosable.

#### Acceptance Criteria

1. THE Parser_Service SHALL define three custom exception classes: `UnsupportedFileError`, `ParserExecutionError`, and `DatabasePersistenceError`, each inheriting from `Exception`.
2. WHEN any unhandled exception occurs inside `process_upload`, THE Parser_Service SHALL log the full traceback at ERROR level before re-raising.
3. THE Upload_Route SHALL catch `UnsupportedFileError`, `ParserExecutionError`, and `DatabasePersistenceError` explicitly before catching bare `Exception`.
4. THE Parser_Service SHALL use the Flask application logger (`current_app.logger`) throughout, not a module-level `logging.getLogger()` logger, to ensure log output respects the app's configured log level and format.

---

### Requirement 10: Backend Tests

**User Story:** As a backend developer, I want automated tests for the parser integration flow, so that regressions are caught before they reach the frontend.

#### Acceptance Criteria

1. THE Test_Suite SHALL be located entirely inside `Backend/tests/` and SHALL NOT modify any file in `Backend/parsers/`.
2. WHEN the upload endpoint is called with a valid `.log` file in a POST request, THE Test_Suite SHALL assert that the HTTP response status is 200 and the response body contains `parseStatus` and `eventCount` keys in `data`.
3. WHEN the upload endpoint is called with an unsupported file extension (e.g. `.exe`), THE Test_Suite SHALL assert that the HTTP response status is 415.
4. WHEN a file is uploaded with a name that maps to a known parser, THE Test_Suite SHALL assert that the correct parser source name is returned by `detect_parser()`.
5. WHEN a file is uploaded with a name that does not match any parser keyword, THE Test_Suite SHALL assert that `detect_parser()` returns the fallback source name `linux_syslog`.
6. WHEN `parse()` raises a `RuntimeError`, THE Test_Suite SHALL assert that the upload endpoint returns HTTP 500 and `parse_status` is set to `failed` in the database.
7. WHEN a valid file is parsed successfully, THE Test_Suite SHALL assert that the number of TimelineEvent rows in the database equals `eventCount` in the response.
8. FOR ALL files in `Backend/parsers/sample_logs/` that have a matching parser, THE Test_Suite SHALL assert that parsing and re-parsing the same file produces the same number of events (idempotence of read-only parse).
