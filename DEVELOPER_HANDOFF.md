# ForenSync Developer Handoff — Timeline Feature

**Date:** February 16, 2025  
**Status:** 43/44 tests passing — 1 failing test in timeline correlation  
**Next Task:** Fix NULL timestamp handling in session correlation

---

## Quick Start

### What's Working
- ✅ Backend parser integration (5 plugins: Auth Log, Linux Syslog, Apache, Nginx, Windows Event Log)
- ✅ File upload and parsing pipeline
- ✅ Timeline generation and event correlation (mostly complete)
- ✅ Timeline API endpoints (generate, retrieve, stats)
- ✅ 43 passing tests covering upload, parsing, and timeline

### What's Broken
- ❌ **1 failing test:** `test_null_timestamps_handled_correctly` in `Backend/tests/test_timeline_correlation.py`
- ❌ **No frontend timeline view** — backend is ready but no UI exists

### Run Tests
```bash
cd Backend
python -m pytest tests/ -v
```

### Start Backend
```bash
cd Backend
python run.py
```

---

## The Failing Test: NULL Timestamp Handling

### Location
`Backend/tests/test_timeline_correlation.py`, line 317-367

### What Should Happen
All events with NULL timestamps should be grouped into a **single** "UNKNOWN" session:
- 1 timestamped event creates session `CASE-XXX-S0000`
- 2 NULL timestamp events **both** go into session `CASE-XXX-UNKNOWN`
- **Expected: 2 total sessions**

### What's Actually Happening
Each NULL timestamp event creates its own session:
- 1 timestamped event → `CASE-XXX-S0000`
- NULL event 1 → `CASE-XXX-UNKNOWN` (or separate session)
- NULL event 2 → Another separate session
- **Actual: 3 total sessions**

### Root Cause
**File:** `Backend/services/timeline_correlation_service.py`  
**Function:** `_correlate_events()`, lines 267-289

The problem is in how the code tracks the NULL session. When processing NULL timestamp events:

```python
# Handle NULL timestamp events
if event.timestamp is None:
    # Group all NULL timestamp events into a single session
    if current_session and current_session.get("is_null_session"):
        current_session["events"].append(event)
    else:
        # Start new NULL timestamp session
        if current_session:
            sessions.append(current_session)

        session_id = _generate_session_id(case_id, len(sessions), is_null=True)
        current_session = {
            "session_id": session_id,
            "events": [event],
            "is_null_session": True
        }
    continue
```

**The Bug:** After processing timestamped events and appending the `current_session` to the `sessions` list, the code loses track of the NULL session. When it encounters another NULL event, it checks `current_session` (which is now a timestamped session or None), doesn't find `is_null_session=True`, and creates a NEW NULL session.

### How to Fix

The logic needs to:
1. Check if a NULL session already exists in the `sessions` list (not just `current_session`)
2. If yes, append to that existing NULL session
3. If no, create the UNKNOWN session only once

**Option 1: Track NULL session separately**
```python
def _correlate_events(sorted_events: list, case_id: str) -> list:
    sessions = []
    current_session = None
    null_session = None  # Track NULL session separately
    
    for event in sorted_events:
        if event.timestamp is None:
            # Always add to the same NULL session
            if null_session is None:
                session_id = _generate_session_id(case_id, len(sessions), is_null=True)
                null_session = {
                    "session_id": session_id,
                    "events": [],
                    "is_null_session": True
                }
            null_session["events"].append(event)
            continue
        
        # ... rest of timestamped event logic ...
    
    # Append null_session at the end if it exists
    if null_session:
        sessions.append(null_session)
    
    return sessions
```

**Option 2: Search for existing NULL session in sessions list**
```python
if event.timestamp is None:
    # Check if UNKNOWN session already exists
    null_session = next((s for s in sessions if s.get("is_null_session")), None)
    if null_session:
        null_session["events"].append(event)
    else:
        # Create new NULL session
        session_id = _generate_session_id(case_id, len(sessions), is_null=True)
        sessions.append({
            "session_id": session_id,
            "events": [event],
            "is_null_session": True
        })
    continue
```

### Test the Fix
```bash
cd Backend
python -m pytest tests/test_timeline_correlation.py::TestTimelineCorrelation::test_null_timestamps_handled_correctly -v
```

---

## System Architecture Overview

### Tech Stack
- **Backend:** Flask (Python), SQLAlchemy ORM
- **Database:** SQLite (development) / Supabase PostgreSQL (production — not yet migrated)
- **Frontend:** React (not yet connected to timeline backend)
- **Testing:** pytest, hypothesis (property-based testing)

### Backend Structure
```
Backend/
├── app.py                      # Flask app factory
├── config.py                   # Environment configs
├── run.py                      # Dev server entry point
├── models/__init__.py          # SQLAlchemy models (LogFile, TimelineEvent, Case, etc.)
├── routes/
│   ├── upload.py               # File upload + parsing trigger
│   ├── timeline.py             # Timeline generate/retrieve/stats endpoints
│   └── ... (auth, cases, plugins, etc.)
├── services/
│   ├── parser_service.py       # Parser integration (detection, invocation, persistence)
│   ├── timeline_correlation_service.py  # Event correlation into sessions
│   └── ... (auth, case, file, notification, etc.)
├── parsers/
│   └── plugins/                # 5 parser plugins (auth, syslog, apache, nginx, evtx)
│       ├── base.py             # BaseParserPlugin
│       ├── registry.py         # Plugin discovery and loading
│       ├── auth_log.py         # SSH/auth log parser
│       ├── linux_syslog.py     # Linux syslog parser
│       ├── apache_access.py    # Apache access log parser
│       ├── nginx_access.py     # Nginx access log parser
│       └── windows_event_log.py # Windows .evtx parser
└── tests/
    ├── conftest.py             # Pytest fixtures
    ├── test_upload_route.py    # Upload endpoint integration tests
    ├── test_parser_service.py  # Parser service unit tests
    ├── test_parser_service_props.py  # Property-based tests
    └── test_timeline_correlation.py  # Timeline correlation tests (1 failing)
```

---

## Database Schema

### Core Tables

**`timeline_events`** — Parsed log events (populated by parser service)
| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Primary key |
| `case_id` | string | FK to cases |
| `log_file_id` | int | FK to log_files (which file this came from) |
| `timestamp` | datetime | Event timestamp (NULL if unparseable) |
| `timestamp_str` | string | Original timestamp string from log |
| `session_id` | string | Session identifier (populated by timeline correlation) |
| `source` | string | Parser that produced this event (e.g., "auth_log") |
| `host` | string | Hostname/machine |
| `actor` | string | Who/what performed the action (IP, username, etc.) |
| `action` | string | What happened (e.g., "ssh_login_failed") |
| `object` | string | What was acted upon (username, file path, etc.) |
| `result` | string | Outcome: "success", "failure", HTTP code, "unknown" |
| `severity` | string | "Critical", "Warning", "Info" (auto-calculated) |
| `description` | string | Human-readable summary |
| `raw_log` | string | **Original untouched log line — always preserved** |

**`log_files`** — File upload metadata
| Column | Type | Description |
|--------|------|-------------|
| `id` | int | Primary key |
| `case_id` | string | FK to cases |
| `filename` | string | Original filename |
| `stored_filename` | string | Saved as `{JOB_ID}_{secure_filename}` |
| `file_size` | int | Bytes |
| `job_id` | string | Unique job identifier (e.g., "JOB-AB12CD34") |
| `parse_status` | string | "queued" → "processing" → "parsed" or "failed" |

**`cases`** — Investigation cases
| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `case_id` | string | Human-readable ID (e.g., "CASE-1042") |
| `name` | string | Case name |
| `description` | string | Case description |
| `incident_from` | date | Incident start date (used for year in syslog parsers) |
| `incident_to` | date | Incident end date |
| `org_id` | uuid | FK to organizations |
| `created_by` | uuid | FK to users (head who created it) |
| `status` | enum | "Active", "Pending", "Closed" |

---

## Parser Integration Flow

```
1. User uploads file via React frontend
   ↓
2. POST /api/v1/upload (multipart: file + optional caseId)
   ↓
3. routes/upload.py validates extension, saves file as {JOB_ID}_{filename}
   ↓
4. Creates LogFile record with parse_status="queued"
   ↓
5. Calls services/parser_service.py:process_upload()
   ↓
6. Parser service:
   - detect_parser(filename) → source name (e.g., "auth_log")
   - get_plugin(source_name) → parser instance
   - Updates parse_status="processing"
   - plugin.parse(filepath) → List[normalized_event_dicts]
   - Maps each event dict to TimelineEvent row
   - Applies severity rules (failure + login = Critical, etc.)
   - Bulk inserts all events
   - Updates parse_status="parsed"
   ↓
7. Returns HTTP 200 { jobId, parseStatus: "parsed", eventCount: N }
```

### Parser Detection Rules (Priority Order)
1. `.evtx` → `windows_event_log`
2. `.log` + "nginx" → `nginx_access`
3. `.log` + "auth" → `auth_log`
4. `.log` + ("syslog" or "linux") → `linux_syslog`
5. `.log` + ("apache" or "access") → `apache_access`
6. `.log` (no keywords) → `linux_syslog` (default fallback)
7. Other extensions → `UnsupportedFileError` (HTTP 422)

### Severity Mapping Rules (Priority Order)
1. `result="failure"` AND ("login" OR "ssh" in action) → **Critical**
2. `result="failure"` → **Warning**
3. `action` in {"root_console_login", "windows_privileged_logon"} → **Warning**
4. Default → **Info**

---

## Timeline Correlation

### What It Does
After files are parsed, timeline generation:
1. Retrieves all parsed events for a case
2. Sorts chronologically (timestamped events first, NULL timestamps last)
3. Groups events into **sessions** based on:
   - Same `actor` (case-sensitive)
   - Same `host` (case-sensitive)
   - Within 30-minute rolling time window
4. Assigns deterministic session IDs:
   - Timestamped sessions: `{case_id}-S0000`, `{case_id}-S0001`, etc.
   - NULL timestamp session: `{case_id}-UNKNOWN`
5. Persists `session_id` back to each `timeline_events` row

### Timeline API Endpoints

**Generate Timeline**
```
POST /api/v1/cases/{case_id}/timeline/generate

Response 200:
{
  "status": "success",
  "data": {
    "caseId": "CASE-1042",
    "eventCount": 42,
    "sessionCount": 5,
    "status": "generated"
  }
}
```

**Retrieve Timeline**
```
GET /api/v1/cases/{case_id}/timeline?actor={actor}&host={host}

Response 200:
{
  "status": "success",
  "data": {
    "caseId": "CASE-1042",
    "eventCount": 42,
    "sessionCount": 5,
    "timeline": [
      {
        "id": 123,
        "timestamp": "2024-01-01T10:00:00Z",
        "sessionId": "CASE-1042-S0000",
        "source": "auth_log",
        "host": "server01",
        "actor": "192.168.1.10",
        "action": "ssh_login_failed",
        "object": "root",
        "result": "failure",
        "severity": "Critical",
        "description": "192.168.1.10 performed ssh_login_failed on root",
        "rawLog": "Jan  1 10:00:00 server01 sshd[1234]: Failed password for root from 192.168.1.10"
      },
      ...
    ]
  }
}
```

**Timeline Statistics**
```
GET /api/v1/cases/{case_id}/timeline/stats

Response 200:
{
  "status": "success",
  "data": {
    "caseId": "CASE-1042",
    "totalEvents": 42,
    "sessionCount": 5,
    "bySeverity": {
      "Critical": 3,
      "Warning": 12,
      "Info": 27
    },
    "bySource": {
      "auth_log": 30,
      "linux_syslog": 12
    },
    "logFilesCount": 2,
    "parseStatus": "timeline_generated"
  }
}
```

### Current Correlation Config
- **Session window:** 30 minutes (rolling)
- **Configurable via:** `TIMELINE_SESSION_WINDOW_MINUTES` in Flask config
- **NULL timestamp handling:** BROKEN (see failing test above)

---

## What's Complete

### ✅ Backend Foundation
- [x] Database models (SQLAlchemy)
- [x] Upload route + file persistence
- [x] Parser service + 5 working plugins
- [x] Parser detection and selection
- [x] Event normalization and severity mapping
- [x] Parse status lifecycle (queued → processing → parsed/failed)
- [x] Comprehensive error handling and logging

### ✅ Timeline Backend
- [x] Timeline correlation service
- [x] Session grouping algorithm (actor + host + time window)
- [x] Deterministic session ID generation
- [x] Timeline API endpoints (generate, retrieve, stats)
- [x] Timeline filtering (by actor, host, source, action)
- [x] Idempotent generation (safe to re-run)

### ✅ Testing
- [x] 27 parser integration tests (all passing)
- [x] 16 timeline correlation tests (15 passing, 1 failing)
- [x] Property-based tests (hypothesis)
- [x] Upload route integration tests
- [x] Parser service unit tests

---

## What's Missing

### ❌ Frontend Timeline View (Critical)
The backend is 100% ready, but there's **no UI** to display timelines. You need:

1. **Generate Timeline Button** in `CaseFilesPage.jsx`
   - Shows after parsing is complete
   - Calls `POST /api/v1/cases/{caseId}/timeline/generate`
   - Displays loading state and success/error messages

2. **Timeline Route & Component**
   - New route: `/cases/:caseId/timeline`
   - New component: `Timeline.jsx` (or similar)
   - Display correlated events chronologically
   - Show session groupings visually
   - Filter controls (actor, host, source, action)
   - Statistics summary (event count, session count, severity breakdown)

3. **Timeline Navigation**
   - Link from Case Files page after timeline is generated
   - Sidebar navigation item (if applicable)

### ❌ NULL Timestamp Fix (Blocker)
Fix the failing test before deploying timeline feature to production.

---

## Test Status

### Passing Tests (43)
```
✅ test_parser_service.py (12 tests)
   - detect_parser() for all parser types
   - _map_severity() for all severity rules
   - Parser selection correctness

✅ test_parser_service_props.py (6 tests)
   - Property-based tests with hypothesis
   - Determinism, totality, coverage

✅ test_upload_route.py (9 tests)
   - Upload endpoint integration
   - Parse status lifecycle
   - Event persistence
   - Severity mapping

✅ test_timeline_correlation.py (15 tests, 1 failing)
   - Chronological ordering ✓
   - Same actor+host within window ✓
   - Beyond window creates new session ✓
   - Different actors create different sessions ✓
   - Different hosts create different sessions ✓
   - NULL timestamp handling ✗ (FAILING)
   - Deterministic session IDs ✓
   - Idempotent generation ✓
   - Timeline retrieval ✓
   - Filtering by actor ✓
   - Filtering by host ✓
   - Statistics endpoint ✓
   - Error handling (case not found, unparsed files, no events) ✓
```

### Run Specific Test
```bash
# Run all tests
python -m pytest tests/ -v

# Run only timeline tests
python -m pytest tests/test_timeline_correlation.py -v

# Run only failing test
python -m pytest tests/test_timeline_correlation.py::TestTimelineCorrelation::test_null_timestamps_handled_correctly -v -s
```

---

## Known Limitations

### Parser Limitations
- **Timezone handling:** Assumed based on log content; auth_log/syslog use `incident_from` year as `starting_year`
- **Clock skew:** Not automatically detected between hosts (acknowledged problem in digital forensics field)
- **Format variants:** Regex validated against specific datasets — significantly different formats may fall through to `unparsed_event`
- **Apache vs Nginx:** Structurally identical logs, cannot distinguish automatically, manual selection required

### System Limitations
- **File size limit:** 50MB (Supabase Free tier cap)
- **Events table:** Treated as regenerable, not permanent evidence (only raw files and timeline output are permanent)
- **Synchronous parsing:** No async task queue — large files block the request

---

## Next Steps for Developer

### Immediate Priority
1. **Fix the failing test** — Update `_correlate_events()` in `timeline_correlation_service.py`
   - See "The Failing Test" section above for details
   - Run test after fix: `pytest tests/test_timeline_correlation.py::TestTimelineCorrelation::test_null_timestamps_handled_correctly -v`

### Medium Priority
2. **Build Frontend Timeline View**
   - Add "Generate Timeline" button to Case Files page
   - Create Timeline component + route
   - Display events chronologically with session groupings
   - Add filtering controls

3. **Integration Testing**
   - Test full flow: upload → parse → generate timeline → view timeline
   - Test with all 5 parser types
   - Test filtering and statistics

### Low Priority
4. **Performance Optimization** (if needed)
   - Async parsing for large files (Celery/RQ)
   - Batch insert optimization
   - Streaming parser support

5. **Enhanced Features** (nice-to-have)
   - Event filtering during parsing
   - Custom severity rules
   - Timeline export (CSV, JSON)
   - Visual timeline graph/chart
   - Insights engine (rule-based anomaly detection)

---

## Useful Commands

### Backend
```bash
# Install dependencies
cd Backend
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=services --cov=routes --cov-report=html

# Start dev server
python run.py

# Test upload via curl
curl -X POST http://localhost:5000/api/v1/upload \
  -F "file=@parsers/sample_logs/auth_log_sample.log" \
  -F "caseId=CASE-1042"

# Generate timeline via curl
curl -X POST http://localhost:5000/api/v1/cases/CASE-1042/timeline/generate

# Retrieve timeline via curl
curl http://localhost:5000/api/v1/cases/CASE-1042/timeline

# Get timeline stats via curl
curl http://localhost:5000/api/v1/cases/CASE-1042/timeline/stats
```

### Database
```bash
# View database (SQLite)
sqlite3 Backend/forensync.db

# List tables
.tables

# View timeline events
SELECT case_id, timestamp, session_id, actor, host, action, severity FROM timeline_events LIMIT 10;

# Count events by session
SELECT session_id, COUNT(*) FROM timeline_events GROUP BY session_id;
```

---

## Documentation References

- **System Handoff:** `ForenSync_System_Handoff.md` (comprehensive system overview)
- **Parser Integration:** `Backend/PARSER_INTEGRATION_SUMMARY.md` (parser implementation details)
- **Spec Files:**
  - `.kiro/specs/backend-parser-integration/requirements.md`
  - `.kiro/specs/backend-parser-integration/design.md`

---

## Contact / Questions

For questions about this handoff or the codebase, review:
1. This document for high-level overview
2. `ForenSync_System_Handoff.md` for full system architecture
3. Test files for concrete examples of expected behavior
4. Code comments in `timeline_correlation_service.py` for correlation algorithm details

Good luck! 🚀
