# ForenSync Backend — Developer Architecture Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Folder Structure](#2-folder-structure)
3. [Architecture Overview](#3-architecture-overview)
4. [Configuration System](#4-configuration-system)
5. [Application Factory](#5-application-factory)
6. [API Endpoints Reference](#6-api-endpoints-reference)
7. [Mock Data — Current State](#7-mock-data--current-state)
8. [Response Envelope](#8-response-envelope)
9. [Validation Layer](#9-validation-layer)
10. [Request Flow](#10-request-flow)
11. [Database Integration Points](#11-database-integration-points)
12. [Parser Integration Points](#12-parser-integration-points)
13. [Service Interfaces to Implement](#13-service-interfaces-to-implement)
14. [Deferred Improvements](#14-deferred-improvements)
15. [Running Locally](#15-running-locally)

---

## 1. Project Overview

ForenSync is a Digital Forensics Timeline Generator. This document covers the
Flask backend only. The React frontend (forensync-ui) is complete and read-only.
The backend must not require any frontend changes.

Current phase: Foundation complete. No database, no parser, no authentication.
Every endpoint returns validated, correctly-shaped JSON so the frontend
can be wired up without changes when real data layers are added.

---

## 2. Folder Structure

```
Backend/
 app.py                  # Application Factory — create_app()
 config.py               # All configuration classes
 run.py                  # Entry point — starts the dev server
 requirements.txt        # Pinned Python dependencies
 .env.example            # Documents every environment variable
 .gitignore              # Python / venv / uploads exclusions

 routes/                 # One Blueprint file per feature area
    __init__.py
    health.py           # GET  /api/v1/health
    auth.py             # POST /api/v1/auth/login|register
    cases.py            # GET|POST /api/v1/cases, GET /api/v1/cases/<id>
    upload.py           # POST /api/v1/upload
    plugins.py          # GET /api/v1/plugins, POST /api/v1/plugins/activate
    settings.py        # GET|PUT /api/v1/settings, POST|DELETE investigators

 services/               # Business logic layer (empty — next phase)
    __init__.py

 utils/                  # Reusable helpers
    __init__.py
    response.py         # success_response() / error_response()
    validators.py       # require_json_fields(), allowed_file(), etc.

 models/                 # SQLAlchemy models (empty — database phase)
    __init__.py

 parsers/                # Parser plugin modules (empty — parser phase)
    __init__.py

 tests/                  # pytest test suite (empty — next phase)
    __init__.py

 uploads/                # Uploaded log files land here
    .gitkeep

 migrations/             # Alembic DB migrations (empty — database phase)
```

---

## 3. Architecture Overview

```
React Frontend (Vite :5173)
        |
        |  HTTP + CORS
        v
Flask Application (run.py -> create_app())
        |
        |-- Flask-CORS middleware (validates Origin header)
        |-- Blueprint router   (matches /api/v1/<resource>)
        |-- View function      (validates input, calls service)
        |-- utils/response.py  (formats JSON envelope)
        |
        v
JSON Response -> React
```

### Design Principles

- Application Factory pattern — `create_app(config_name)` builds the app.
  Nothing is initialised at import time, making the app fully testable.
- Blueprint-per-resource — each feature area is isolated. Adding a feature
  means creating one new file in routes/ and one line in `_register_blueprints`.
- Centralized response shape — all endpoints use `success_response()` or
  `error_response()`. The frontend can always check `response.status`.
- Config-driven — every setting comes from an environment variable.
  No hardcoded values in application code.
- Fail-fast in production — ProductionConfig raises EnvironmentError at
  startup if SECRET_KEY is missing rather than running insecurely.

---

## 4. Configuration System

File: `config.py`

### Class hierarchy

```
BaseConfig          shared defaults for all environments
  |-- DevelopmentConfig    DEBUG=True, LOG_LEVEL=DEBUG
  |-- TestingConfig         TESTING=True, isolated upload folder, quiet logs
  -- ProductionConfig      DEBUG=False, enforces SECRET_KEY presence
```

### Config registry

```python
config_map = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
```

`create_app(config_name)` calls `config_map.get(config_name)` — no if/else.

### Key settings

| Setting              | Default              | Source env var   |
|----------------------|----------------------|------------------|
| SECRET_KEY           | dev-insecure-placeholder | SECRET_KEY   |
| DEBUG                | False (True in dev)  | FLASK_ENV        |
| UPLOAD_FOLDER        | ./uploads (abs path) | UPLOAD_FOLDER    |
| MAX_CONTENT_LENGTH   | 52428800 (50 MB)     | hardcoded        |
| ALLOWED_EXTENSIONS   | log,txt,csv,json,xml,evtx,pcap | hardcoded |
| CORS_ORIGINS         | http://localhost:5173 | CORS_ORIGINS    |
| LOG_LEVEL            | DEBUG (WARNING prod) | FLASK_ENV        |
| LOG_FORMAT           | timestamp level name msg | hardcoded    |

---

## 5. Application Factory

File: `app.py` — function `create_app(config_name: str = "default")`

### Startup sequence (in order)

```
1. load_dotenv()              reads .env file into os.environ
2. Flask(__name__)            creates the Flask instance
3. app.config.from_object()  applies the Config class
4. os.makedirs(UPLOAD_FOLDER) ensures uploads/ directory exists
5. _configure_logging()       StreamHandler with format + level from config
6. CORS(app, ...)             flask-cors with origins/methods/headers from config
7. _register_blueprints()     imports and registers all 6 blueprints
8. _register_error_handlers() 400/404/405/413/422/500 + bare Exception
```

### Error handler behaviour

All unhandled errors return the standard JSON error envelope.
In development, the real exception message is included.
In production, a generic "An unexpected error occurred." message is returned.
Full stack traces are always logged via `app.logger.error`.

---

## 6. API Endpoints Reference

All routes are prefixed with `/api/v1/`. CORS is enabled for all routes.

---

### GET /api/v1/health

Purpose: Liveness check. Confirms the server is running.
Auth required: No
Mock data: No — always reflects real runtime state.

Request: No body required.

Response 200:
```json
{
  "status": "success",
  "message": "OK",
  "data": {
    "app": "ForenSync",
    "version": "0.1.0",
    "environment": "development"
  }
}
```

---

### POST /api/v1/auth/login

Purpose: Authenticate a user by org ID, user ID, and role.
Auth required: No
Mock data: YES — returns hardcoded user data, no DB lookup.

Request body (JSON):
```json
{
  "orgId":  "ORG-XXXX",
  "userId": "INV-XXXX",
  "role":   "investigator"
}
```

Field rules:
- orgId: required, string
- userId: required, string (INV- or HEAD- prefix expected)
- role: required, must be "investigator" or "head"

Response 200:
```json
{
  "status": "success",
  "message": "Login successful.",
  "data": {
    "role": "investigator",
    "name": "Aditi Rao",
    "investigatorId": "INV-2291",
    "orgId": "ORG-4410",
    "orgName": "Sentinel Cyber Forensics"
  }
}
```

Response 400 (missing fields):
```json
{
  "status": "error",
  "error": "Bad Request",
  "message": "Missing required fields.",
  "errors": [{ "field": "orgId", "message": "This field is required." }]
}
```

---

### POST /api/v1/auth/register

Purpose: Register a new organization with head + investigators.
Auth required: No
Mock data: YES — echoes input back, no DB insert.

Request body (JSON):
```json
{
  "orgName":    "Sentinel Cyber Forensics",
  "orgId":      "ORG-4410",
  "orgHeadId":  "HEAD-0001",
  "investigators": [
    { "name": "Aditi Rao", "id": "INV-2291" }
  ]
}
```

Field rules:
- orgName: required
- orgId: required, must match ORG-{alphanumeric} format
- orgHeadId: required, must match HEAD-{alphanumeric} format
- investigators: optional array

Response 201:
```json
{
  "status": "success",
  "message": "Organization registered successfully.",
  "data": {
    "orgId": "ORG-4410",
    "orgName": "Sentinel Cyber Forensics",
    "orgHeadId": "HEAD-0001",
    "investigators": []
  }
}
```

---

### GET /api/v1/cases

Purpose: List all cases for the authenticated organization.
Auth required: No (will require auth after auth phase)
Mock data: YES — returns 5 hardcoded cases matching mockData.js.

Request: No body required.

Response 200:
```json
{
  "status": "success",
  "message": "OK",
  "data": {
    "total": 5,
    "cases": [
      {
        "caseId": "CASE-1042",
        "name": "Unauthorized SSH Access — prod-web-03",
        "timeframe": "02 Jul – 05 Jul 2026",
        "lastModified": "2026-07-09 18:22",
        "status": "Active",
        "action": "Open"
      }
    ]
  }
}
```

---

### POST /api/v1/cases

Purpose: Create a new forensic case.
Auth required: No (will require auth after auth phase)
Mock data: YES — returns hardcoded CASE-1099, no DB insert.

Accepts: multipart/form-data OR application/json

Fields:
- name: required
- description: optional
- from: optional (YYYY-MM-DD)
- to: optional (YYYY-MM-DD)
- files[]: optional (multipart only — not saved yet)

Response 201:
```json
{
  "status": "success",
  "message": "Case created successfully.",
  "data": {
    "caseId": "CASE-1099",
    "name": "My Case",
    "description": "",
    "timeframe": "2026-07-01 – 2026-07-05",
    "lastModified": "just now",
    "status": "Active",
    "action": "Open"
  }
}
```

---

### GET /api/v1/cases/<case_id>

Purpose: Fetch a single case by ID.
Auth required: No
Mock data: YES — searches the in-memory _MOCK_CASES list.

Response 200:
```json
{
  "status": "success",
  "message": "OK",
  "data": {
    "case": { ...case object... }
  }
}
```

Response 404:
```json
{
  "status": "error",
  "error": "Not Found",
  "message": "Case 'CASE-9999' not found."
}
```

---

### POST /api/v1/upload

Purpose: Upload a log file and queue it for parsing.
Auth required: No
Mock data: YES — file is received and validated but NOT saved to disk.
           Returns a mock job ID.

Request: multipart/form-data
- file: required — the binary log file
- caseId: optional — associate with an existing case

Validation performed (real, not mocked):
1. File field must be present
2. Filename must not be empty
3. Filename safety check (no path traversal, no null bytes, max 255 chars)
4. Extension must be in ALLOWED_EXTENSIONS (log, txt, csv, json, xml, evtx, pcap)

Response 200:
```json
{
  "status": "success",
  "message": "File received and queued for processing.",
  "data": {
    "filename": "auth.log",
    "size": 4096,
    "caseId": "CASE-1099",
    "jobId": "JOB-MOCK-001",
    "parseStatus": "queued"
  }
}
```

Response 415 (bad extension):
```json
{
  "status": "error",
  "error": "Unsupported Media Type",
  "message": "File type not allowed. Accepted extensions: csv, evtx, json, log, pcap, txt, xml."
}
```

---

### GET /api/v1/plugins

Purpose: Return the active parser plugin and all supported formats.
Auth required: No
Mock data: YES — in-memory _active_plugin (starts as null) and hardcoded formats.

Response 200:
```json
{
  "status": "success",
  "message": "OK",
  "data": {
    "currentPlugin": null,
    "supportedFormats": [
      { "id": "linux-auth",    "label": "Linux Auth Log Parser" },
      { "id": "apache-access", "label": "Apache Access Log Parser" },
      { "id": "custom",        "label": "Develop Custom Plugin" }
    ]
  }
}
```

---

### POST /api/v1/plugins/activate

Purpose: Set the active parser plugin for the organization.
Auth required: No
Mock data: YES — updates in-memory variable, not persisted.

Request body (JSON):
```json
{ "pluginId": "linux-auth" }
```

Valid pluginId values: "linux-auth", "apache-access", "custom"

Response 200:
```json
{
  "status": "success",
  "message": "Plugin activated.",
  "data": {
    "currentPlugin": { "name": "Linux Auth Log Parser", "addedOn": "today" }
  }
}
```

Response 404 (unknown plugin):
```json
{
  "status": "error",
  "error": "Not Found",
  "message": "Unknown plugin ID: 'bad-id'. Valid IDs: ['linux-auth', 'apache-access', 'custom']"
}
```

---

### GET /api/v1/settings

Purpose: Fetch org profile and investigator list.
Auth required: No (will require "head" role after auth phase)
Mock data: YES — hardcoded org and investigators matching mockData.js.

Response 200:
```json
{
  "status": "success",
  "message": "OK",
  "data": {
    "org": { "orgName": "Sentinel Cyber Forensics", "orgId": "ORG-4410" },
    "investigators": [
      { "name": "Aditi Rao",   "id": "INV-2291" },
      { "name": "Rohan Mehta", "id": "INV-2287" }
    ]
  }
}
```

---

### PUT /api/v1/settings

Purpose: Update the organization name.
Auth required: No (will require "head" role after auth phase)
Mock data: YES — updates in-memory dict, not persisted.

Request body (JSON):
```json
{ "orgName": "New Org Name" }
```

Response 200:
```json
{
  "status": "success",
  "message": "Settings updated.",
  "data": { "org": { "orgName": "New Org Name", "orgId": "ORG-4410" } }
}
```

---

### POST /api/v1/settings/investigators

Purpose: Add a new investigator to the organization.
Auth required: No (will require "head" role after auth phase)
Mock data: YES — appends to in-memory list, not persisted.

Request body (JSON):
```json
{ "name": "Jane Doe", "id": "INV-9999" }
```

Field rules:
- name: required
- id: required, must match INV-{alphanumeric} format

Response 201:
```json
{
  "status": "success",
  "message": "Investigator added.",
  "data": { "investigators": [ ...updated list... ] }
}
```

Response 409 (duplicate ID):
```json
{
  "status": "error",
  "error": "Conflict",
  "message": "Investigator ID 'INV-2291' already exists."
}
```

---

### DELETE /api/v1/settings/investigators/<inv_id>

Purpose: Remove an investigator from the organization.
Auth required: No (will require "head" role after auth phase)
Mock data: YES — removes from in-memory list, not persisted.

Response 200:
```json
{
  "status": "success",
  "message": "Investigator removed.",
  "data": { "investigators": [ ...updated list... ] }
}
```

Response 404:
```json
{
  "status": "error",
  "error": "Not Found",
  "message": "Investigator 'INV-9999' not found."
}
```

---

## 7. Mock Data — Current State

| Endpoint                              | Returns mock data? | What is mocked                              |
|---------------------------------------|--------------------|---------------------------------------------|
| GET  /api/v1/health                   | No                 | Real runtime state                          |
| POST /api/v1/auth/login               | Yes                | Hardcoded user name + org name              |
| POST /api/v1/auth/register            | Yes                | Echoes input back, no uniqueness check      |
| GET  /api/v1/cases                    | Yes                | 5 hardcoded cases from _MOCK_CASES          |
| POST /api/v1/cases                    | Yes                | Returns CASE-1099, not saved to DB          |
| GET  /api/v1/cases/<id>               | Yes                | Searches _MOCK_CASES in memory              |
| POST /api/v1/upload                   | Partial            | Validates file, reads size, does NOT save   |
| GET  /api/v1/plugins                  | Yes                | Hardcoded formats, in-memory active state   |
| POST /api/v1/plugins/activate         | Yes                | In-memory only, resets on server restart    |
| GET  /api/v1/settings                 | Yes                | Hardcoded org + investigator list           |
| PUT  /api/v1/settings                 | Yes                | In-memory only, resets on server restart    |
| POST /api/v1/settings/investigators   | Yes                | In-memory only, resets on server restart    |
| DELETE /api/v1/settings/investigators | Yes                | In-memory only, resets on server restart    |

Note: /api/v1/upload performs REAL validation (filename safety, extension check,
size measurement). Only the save-to-disk and job-creation steps are mocked.

---

## 8. Response Envelope

File: `utils/response.py`

Every endpoint returns one of these two shapes. The frontend can always
branch on `response.data.status`.

### Success

```json
{
  "status":  "success",
  "message": "Human readable description",
  "data":    { }
}
```

### Error

```json
{
  "status":  "error",
  "error":   "Short Error Name",
  "message": "Human readable explanation",
  "errors":  [ { "field": "fieldName", "message": "Why it failed." } ]
}
```

The `errors` array is only present when the endpoint provides field-level
validation details (e.g. form submissions). It is absent on server errors.

### Helper functions

```python
success_response(data=None, message="OK", status_code=200)
error_response(message, status_code, error="Error", errors=None)
```

Both return a `(Flask Response, int)` tuple compatible with Flask view returns.

---

## 9. Validation Layer

File: `utils/validators.py`

Centralized input validation keeps route files thin. Every validator
returns `(is_valid: bool, errors: list[dict])`.

| Function               | Use case                                          |
|------------------------|---------------------------------------------------|
| require_json_fields()  | Check required keys exist in a JSON body          |
| require_form_fields()  | Check required keys exist in multipart form data  |
| allowed_file()         | Check filename extension is in ALLOWED_EXTENSIONS |
| safe_filename_check()  | Reject path traversal, null bytes, long names     |
| validate_id_format()   | Enforce ORG-/INV-/HEAD- prefix+alphanumeric format|

Usage pattern in every route:
```python
valid, errors = require_json_fields(request, ["orgId", "userId"])
if not valid:
    return error_response("Missing required fields.", 400, errors=errors)
```

---

## 10. Request Flow

### Current flow (mock phase)

```
React (fetch/axios call)
  |
  | HTTP request to http://localhost:5000/api/v1/<route>
  v
Flask-CORS middleware
  | Checks Origin header against CORS_ORIGINS list
  | Returns 403 if origin not allowed
  | Returns Access-Control-Allow-* headers if allowed
  v
Flask URL router
  | Matches route to Blueprint view function
  | Returns 404 JSON if no route matches
  | Returns 405 JSON if method not allowed
  v
View function (routes/*.py)
  | 1. Reads request body (get_json or request.form)
  | 2. Calls validators (require_json_fields, etc.)
  | 3. Returns 400 error_response if validation fails
  | 4. [Currently] Returns mock data via success_response
  v
utils/response.py
  | Wraps payload in { status, message, data } envelope
  | Sets Content-Type: application/json
  v
React receives JSON response
```

### Future flow (after all phases complete)

```
React (fetch/axios call with JWT token in Authorization header)
  |
  v
Flask-CORS middleware
  v
JWT auth middleware (auth phase)
  | Validates token, extracts user/org identity
  | Returns 401 if token missing or invalid
  v
Role guard decorator (auth phase)
  | Checks user role against required role for route
  | Returns 403 if insufficient permissions
  v
View function
  | 1. Validates input
  | 2. Calls Service layer (services/*.py)
  v
Service layer (database phase)
  | 3. Queries PostgreSQL via SQLAlchemy models
  | 4. Returns domain objects
  v
View function
  | 5. For upload routes — dispatches to parser layer
  v
Parser layer (parser phase)
  | 6. PluginRegistry selects active plugin
  | 7. Plugin parses file, extracts timeline events
  | 8. Events written to database
  | 9. Returns job status / parsed event count
  v
View function
  | 10. Calls success_response(data=result)
  v
utils/response.py
  v
React receives real data
```

---

## 11. Database Integration Points

When PostgreSQL + SQLAlchemy are added, these are the exact locations
to replace stub code. Each location has a matching TODO comment in source.

### routes/auth.py — login()

```python
# REPLACE THIS:
return success_response(data={"name": "Aditi Rao", ...})

# WITH THIS:
user = UserService.get_by_org_and_id(org_id, user_id, role)
if not user:
    return error_response("Invalid credentials.", 401, error="Unauthorized")
token = TokenService.generate(user)
return success_response(data={**user.to_dict(), "token": token})
```

### routes/auth.py — register()

```python
# REPLACE THIS:
return success_response(data={...echoed input...})

# WITH THIS:
if OrgService.exists(org_id):
    return error_response("Org ID already registered.", 409, error="Conflict")
org = OrgService.create(name, org_id, org_head, investigators)
return success_response(data=org.to_dict(), status_code=201)
```

### routes/cases.py — list_cases()

```python
# REPLACE THIS:
return success_response(data={"cases": _MOCK_CASES, "total": len(_MOCK_CASES)})

# WITH THIS:
org_id = get_current_user_org()
cases  = CaseService.list(org_id=org_id)
return success_response(data={"cases": [c.to_dict() for c in cases], "total": len(cases)})
```

### routes/cases.py — create_case()

```python
# REPLACE THIS:
new_case = {"caseId": "CASE-1099", ...}

# WITH THIS:
case = CaseService.create(name=name, description=description,
                          date_from=date_from, date_to=date_to,
                          org_id=get_current_user_org())
return success_response(data=case.to_dict(), status_code=201)
```

### routes/cases.py — get_case()

```python
# REPLACE THIS:
case = next((c for c in _MOCK_CASES if c["caseId"] == case_id), None)

# WITH THIS:
case = CaseService.get(case_id)
```

### routes/upload.py — upload_file()

```python
# REPLACE THIS (size-only mock):
uploaded.stream.seek(0, 2); file_size = uploaded.stream.tell()

# WITH THIS:
from werkzeug.utils import secure_filename
safe_name  = secure_filename(uploaded.filename)
save_path  = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)
uploaded.save(save_path)
file_size  = os.path.getsize(save_path)
case       = CaseService.get_by_id(case_id)
job        = ParserJobService.create(case_id=case.id, filepath=save_path)
```

### routes/plugins.py — list_plugins() and activate_plugin()

```python
# REPLACE in-memory _active_plugin and _SUPPORTED_FORMATS with:
active  = PluginService.get_active(org_id=get_current_user_org())
formats = PluginService.list_supported()
# and:
PluginService.set_active(org_id=get_current_user_org(), plugin_id=plugin_id)
```

### routes/settings.py — all four endpoints

```python
# REPLACE _org and _investigators dicts with:
org     = OrgService.get(org_id)
members = InvestigatorService.list(org_id=org_id)
# writes:
OrgService.update(org_id, name=org_name)
InvestigatorService.create(name, inv_id, org_id)
InvestigatorService.delete(inv_id, org_id)
```

---

## 12. Parser Integration Points

Parser logic plugs in at two locations only.

### Location 1 — routes/upload.py after file is saved

```python
# After job = ParserJobService.create(...):
plugin = PluginRegistry.get_active(org_id=get_current_user_org())
if plugin is None:
    return error_response("No active parser plugin. Please activate one.", 422)
plugin.enqueue(filepath=save_path, job_id=job.id)
```

### Location 2 — routes/plugins.py activate_plugin()

```python
# After PluginService.set_active(...):
ok, err = PluginRegistry.validate(plugin_id)
if not ok:
    return error_response(f"Plugin failed health check: {err}", 500,
                          error="Plugin Error")
```

### Parser architecture (to be built)

```
parsers/
 __init__.py
 base_parser.py        # Abstract BaseParser class
 registry.py           # PluginRegistry — loads and validates plugins
 linux_auth.py         # LinuxAuthParser(BaseParser)
 apache_access.py      # ApacheAccessParser(BaseParser)
 custom/               # Drop-in folder for user-supplied parsers
```

`BaseParser` interface (to define):
```python
class BaseParser:
    def can_parse(self, filepath: str) -> bool: ...
    def parse(self, filepath: str) -> list[TimelineEvent]: ...
    def validate(self) -> tuple[bool, str]: ...
```

`TimelineEvent` shape (to define):
```python
@dataclass
class TimelineEvent:
    timestamp: datetime
    event_type: str
    source_ip: str | None
    target_user: str | None
    raw_line: str
    case_id: str
    job_id: str
```

---

## 13. Service Interfaces to Implement

These service classes live in `services/` and form the bridge between
routes and the database. Routes call services; services call models.

### UserService (services/user_service.py)

```python
class UserService:
    @staticmethod
    def get_by_org_and_id(org_id: str, user_id: str, role: str) -> User | None: ...
    @staticmethod
    def authenticate(org_id: str, user_id: str, role: str) -> User | None: ...
```

### OrgService (services/org_service.py)

```python
class OrgService:
    @staticmethod
    def exists(org_id: str) -> bool: ...
    @staticmethod
    def get(org_id: str) -> Org | None: ...
    @staticmethod
    def create(name: str, org_id: str, head_id: str, investigators: list) -> Org: ...
    @staticmethod
    def update(org_id: str, name: str) -> Org: ...
```

### InvestigatorService (services/investigator_service.py)

```python
class InvestigatorService:
    @staticmethod
    def list(org_id: str) -> list[Investigator]: ...
    @staticmethod
    def exists(inv_id: str) -> bool: ...
    @staticmethod
    def create(name: str, inv_id: str, org_id: str) -> Investigator: ...
    @staticmethod
    def delete(inv_id: str, org_id: str) -> bool: ...
```

### CaseService (services/case_service.py)

```python
class CaseService:
    @staticmethod
    def list(org_id: str) -> list[Case]: ...
    @staticmethod
    def get(case_id: str) -> Case | None: ...
    @staticmethod
    def create(name: str, description: str, date_from: str,
               date_to: str, org_id: str) -> Case: ...
```

### ParserJobService (services/parser_job_service.py)

```python
class ParserJobService:
    @staticmethod
    def create(case_id: str, filepath: str) -> ParserJob: ...
    @staticmethod
    def get_status(job_id: str) -> dict: ...
    @staticmethod
    def update_status(job_id: str, status: str, event_count: int = 0) -> None: ...
```

### PluginService (services/plugin_service.py)

```python
class PluginService:
    @staticmethod
    def list_supported() -> list[Plugin]: ...
    @staticmethod
    def get(plugin_id: str) -> Plugin | None: ...
    @staticmethod
    def get_active(org_id: str) -> Plugin | None: ...
    @staticmethod
    def set_active(org_id: str, plugin_id: str) -> None: ...
```

### TokenService (services/token_service.py)

```python
class TokenService:
    @staticmethod
    def generate(user: User) -> str: ...
    @staticmethod
    def verify(token: str) -> User | None: ...
```

---

## 14. Deferred Improvements

These improvements are intentionally deferred until after database and
parser integration is complete. Do not implement them in the foundation phase.

### Authentication middleware

Currently all endpoints are open. After the auth phase:
- Add `@require_auth` decorator that validates the JWT token
- Add `@require_role("head")` decorator for settings endpoints
- Token should be passed in `Authorization: Bearer <token>` header
- `get_current_user_org()` helper should read org from the decoded token

### Pagination for GET /api/v1/cases

The cases list endpoint currently returns all cases. After DB integration:
- Add `?page=1&per_page=20` query parameters
- Return `{ cases, total, page, per_page, pages }` in the data envelope

### Job polling endpoint

Upload queues a parse job but there is no way to check its status.
Add after parser phase:
- `GET /api/v1/jobs/<job_id>` — returns `{ jobId, status, eventCount, errors }`

### Timeline endpoint

The core product output. Add after parser phase:
- `GET /api/v1/cases/<case_id>/timeline` — returns sorted TimelineEvent list

### File storage abstraction

Currently files would be saved to the local filesystem.
Consider abstracting behind a `StorageBackend` interface so S3 or
similar can be swapped in without changing the upload route.

### Request ID tracing

Add a unique `X-Request-ID` header to every response for log correlation.
One line change in `utils/response.py` once the pattern is established.

### Rate limiting

Add `flask-limiter` to the auth endpoints (login/register) to prevent
brute-force attacks. Defer until auth is real.

### Input sanitization

`validators.py` checks presence and format. After DB integration, add:
- String length limits on name fields
- Date format validation (YYYY-MM-DD) for case timeframe fields
- File MIME type sniffing in addition to extension check

---

## 15. Running Locally

```bash
# 1. Activate the virtual environment (Windows)
forenSync\Backend\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment file
copy .env.example .env

# 4. Start the backend
python run.py
# Server running on http://0.0.0.0:5000

# 5. Verify it is working
curl http://localhost:5000/api/v1/health
# Expected: {"data":{"app":"ForenSync","environment":"development","version":"0.1.0"},"message":"OK","status":"success"}

# 6. Test the cases list
curl http://localhost:5000/api/v1/cases
# Expected: {"data":{"cases":[...],"total":5},"message":"OK","status":"success"}

# 7. Test a login
curl -X POST http://localhost:5000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d "{\"orgId\":\"ORG-4410\",\"userId\":\"INV-2291\",\"role\":\"investigator\"}"
```

### Environment variables (copy from .env.example)

| Variable       | Required | Description                          |
|----------------|----------|--------------------------------------|
| FLASK_ENV      | Yes      | development / testing / production   |
| FLASK_APP      | Yes      | run.py                               |
| SECRET_KEY     | Prod only| Long random string for session signing|
| CORS_ORIGINS   | No       | Comma-separated list, default :5173  |
| UPLOAD_FOLDER  | No       | Path to uploads dir, default ./uploads|
| FLASK_RUN_HOST | No       | Default 0.0.0.0                      |
| FLASK_RUN_PORT | No       | Default 5000                         |

---

*Document generated from source — reflects backend state as of foundation phase.*
*Update this file when service layer, database models, or parser modules are added.*
