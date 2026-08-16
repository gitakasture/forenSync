# ForenSync — System Handoff Document
### Everything built so far, and what's needed for Timeline Generation & Correlation

This document exists so any teammate can understand the full system — frontend, backend, database — without needing to ask Vinita to explain it in person. Read top to bottom for the full picture, or jump to a section using the headers.

**📋 For next developer: See `DEVELOPER_HANDOFF.md` for quick start guide, failing test details, and immediate next steps.**

---

## 1. System Overview

ForenSync has two user roles, each with their own dashboard and permissions:

| Role | Can do |
|---|---|
| **Head of Team** | Create cases, assign investigators, view all cases they created, manage the organization's plugin catalog, view org-wide activity |
| **Investigator** | View cases assigned to them, confirm assignments, upload case files, match parsers, parse files, (next: view generated timeline) |

Both roles log in through the same page, are routed to different dashboards, and share most UI components (Sidebar, TopBar) with role-based conditional rendering.

---

## 2. Database Schema (Supabase / PostgreSQL)

### `organizations`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `org_id` | text | Human-readable ID, e.g. `"ORG-4410"` |
| `name` | text | |
| `is_active` | bool | |
| `created_at` | timestamptz | |

### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `user_id` | text | Human-readable ID, e.g. `"HEAD-0001"` or `"INV-2291"` |
| `name` | text | |
| `role` | enum | `'head'` or `'investigator'` |
| `status` | enum | `'Active'` or `'Inactive'` |
| `org_id` | uuid | FK → `organizations.id` |
| `created_at`, `updated_at` | timestamptz | |

**Important:** Head accounts are manually seeded directly in Supabase — there is no self-registration flow for heads. The `/register` endpoint only adds investigators to an org whose head already exists.

### `cases`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `case_id` | text | Human-readable, e.g. `"CASE-1042"` |
| `name`, `description` | text | |
| `priority` | enum | `case_priority` |
| `status` | enum | `case_status` — `Active` / `Pending` / `Closed` |
| `incident_from`, `incident_to` | date | Investigator-provided incident timeframe (used as `starting_year` for syslog-style parsers) |
| `org_id` | uuid | FK → `organizations.id` |
| `created_by` | uuid | FK → `users.id` (the head who created it) |
| `created_at`, `updated_at` | timestamptz | |

### `case_investigators` (many-to-many join table)
| Column | Type | Notes |
|---|---|---|
| `case_id` | uuid | FK → `cases.id` |
| `user_id` | uuid | FK → `users.id` |
| `status` | text | `'pending'` (assigned, not yet confirmed) or `'confirmed'` |
| `assigned_at` | timestamptz | |

**This table is the real source of truth for "which cases does this investigator see."** A case only appears in an investigator's case list once their row here is `'confirmed'`.

### `notifications`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `user_id` | uuid | FK → `users.id` — the recipient |
| `text` | text | Human-readable message |
| `is_read` | bool | Flips to `true` when the investigator confirms |
| `related_case_id` | uuid | FK → `cases.id` (nullable) |
| `created_at` | timestamptz | |

### `case_files`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `case_id` | uuid | FK → `cases.id` |
| `uploaded_by` | uuid | FK → `users.id` |
| `file_name` | text | Original filename |
| `storage_path` | text | Path inside the Supabase Storage bucket |
| `file_category` | text | `'log'` (required, gets parsed) or `'other'` (optional, evidence only, never parsed) |
| `file_size` | bigint | Bytes |
| `uploaded_at` | timestamptz | |

### `org_plugins`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `org_id` | uuid | FK → `organizations.id` |
| `plugin_name` | text | Matches a key in the Python `PLUGIN_REGISTRY` (e.g. `"auth_log"`) |
| `added_at` | timestamptz | |

**This is the "Plugin Marketplace" table.** An org has no plugins active by default — a head must add each one from the Plugins page before it can be matched/used for parsing.

### `events`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `case_id` | uuid | FK → `cases.id` |
| `case_file_id` | uuid | FK → `case_files.id` — which uploaded file this event came from |
| `source` | text | Which plugin produced it, e.g. `"auth_log"` |
| `host`, `actor`, `action`, `object`, `result` | text | The standard event schema fields (see Section 5) |
| `raw_log` | text | Original untouched line/record — always preserved |
| `raw_log_hash` | text | SHA-256 of `raw_log`, for integrity |
| `timestamp` | timestamptz | Nullable — `null` if the parser couldn't determine a timestamp |
| `session_id` | text | **Nullable, not yet populated** — this is what Timeline/Clustering needs to fill in |
| `created_at` | timestamptz | |

**This table is currently treated as re-generatable, not permanent.** Parsing a case's files always clears (`DELETE`) and re-inserts that case's events first — so re-running "Parse Log Files" is safe and idempotent.

### `activity_log`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `org_id` | uuid | FK → `organizations.id` |
| `actor_user_id` | uuid | FK → `users.id` — who performed the action |
| `action_type` | text | e.g. `"case_created"`, `"investigator_confirmed"`, `"files_uploaded"` |
| `description` | text | Human-readable, shown directly in Recent Activity |
| `related_case_id` | uuid | Nullable |
| `created_at` | timestamptz | |

Powers the head dashboard's "Recent Activity" feed — real data, not mock.

### Supabase Storage
**Bucket: `case-files`** (private — backend uses the service role key to access it)
Path structure: `{org_id}/{case_id}/{category}/{uuid}_{filename}`

---

## 3. Backend Architecture

**Framework:** Flask. **Pattern:** thin route handlers → all logic lives in `services/`, which talk directly to Supabase.

```
routes/
  auth.py          → /auth/register, /auth/login
  users.py         → /users (list org members)
  cases.py         → /cases (list/create/get), /cases/<id>/files, /activity
  notifications.py → /notifications, /notifications/<id>/confirm
  plugins.py       → /plugins (list/add/remove), /cases/<id>/match-parsers,
                      /cases/<id>/parse-files, /cases/<id>/parse-status

services/
  auth_service.py       → register_organization(), login_user(), Supabase client singleton
  user_service.py        → list_users()
  case_service.py         → create_case(), list_cases_for_investigator(),
                            list_cases_for_head(), get_case_detail(),
                            _build_display_case() [shared formatter]
  notification_service.py → list_notifications(), confirm_case_assignment()
  activity_service.py     → log_activity(), list_recent_activity()
  file_service.py         → upload_case_files(), list_case_files()
  plugin_service.py       → list_plugins_for_org(), add_plugin_to_org(),
                            remove_plugin_from_org(), match_parsers_for_case()
  parsing_service.py      → parse_case_files(), get_parse_status_for_case()
```

**Custom exceptions** (defined in `auth_service.py`, reused everywhere): `NotFoundError`, `ConflictError`, `ForbiddenError`, `ServiceError`.

---

## 4. The Parser Plugin System (Python)

Located in `plugins/`. Five working, tested plugins, all implementing `BaseParserPlugin`:

| Plugin | File | Input type | Notes |
|---|---|---|---|
| Auth Log (SSH) | `auth_log.py` | Text | Multi-pattern regex, needs `starting_year` |
| Linux Syslog | `linux_syslog.py` | Text | Multi-pattern regex, needs `starting_year` |
| Apache Access | `apache_access.py` | Text | Single regex, full timestamp built in |
| Nginx Access | `nginx_access.py` | Text | Identical format to Apache |
| Windows Event Log | `windows_event_log.py` | Binary `.evtx` | Uses the `evtx` library, JSON field-mapping instead of regex |

**Every plugin's `parse()` returns the same shape** — a list of dicts matching the standard schema (Section 5). Every plugin has a **catch-all fallback** (`unparsed_event`) — no line/record is ever silently dropped.

**`plugins/registry.py`** is the single entry point everything else uses:
- `get_plugin(name, **kwargs)` — instantiate a plugin by name
- `list_available_plugins()` — all registered plugin names
- `detect_format(file_bytes)` — runs real content-based format detection (reuses each plugin's actual `DETECTION_PATTERNS`, not a separate guessing system) and returns ranked `(name, confidence)` pairs
- `PLUGIN_CATALOG` — display metadata (label, description) for the Plugins page

**Known limitation:** Apache and Nginx access logs are structurally identical, so detection will always tie between them — this is expected, not a bug, and the UI lets the investigator manually pick.

---

## 5. Standard Event Schema

Every plugin, and every row in the `events` table, uses this shape:

```
timestamp   — ISO 8601 UTC, e.g. "2005-12-10T06:55:46Z" (or null if undeterminable)
source      — which plugin produced it, e.g. "auth_log"
host        — hostname/machine
actor       — who/what performed the action (IP, username, uid, etc.)
action      — what happened, e.g. "ssh_login_failed"
object      — what was acted upon (username, file path, etc.)
result      — outcome — "success" / "failure" / an HTTP status code / "unknown"
raw_log     — original untouched line/record — ALWAYS preserved, never lost
```

---

## 6. Frontend Page Map

| Page | Route | Role | Purpose |
|---|---|---|---|
| `Login.jsx` | `/login` | Both | Org ID + User ID + role → calls `/auth/login`, stores full response via `setUser()` |
| `Register.jsx` | `/register` | — | Adds investigators to an existing org+head |
| `HeadDashboard.jsx` | `/head-dashboard` | Head | Active cases (created by this head), Quick Actions, real Recent Activity |
| `InvDashboard.jsx` | `/investigator-dashboard` | Investigator | Pending Assignments (unconfirmed notifications), Active Cases (confirmed only) |
| `Cases.jsx` | `/cases` | Both | Full case list, role-aware (created-by for head, confirmed-assigned for investigator) |
| `CaseFilesPage.jsx` | `/cases/:caseId/files` | Investigator | Case details, uploaded log files, Match Parsers, Parse Log Files, Save/Cancel — **state restores from DB on reload** |
| `Plugins.jsx` | `/plugins` | Investigator (sidebar) | Full marketplace — Add/Remove plugins per org |
| `UsersTeams.jsx` | `/users` | Both | Org member list (uses same `/users` endpoint as the investigator-picker) |
| `SystemSettings.jsx`, `Help.jsx` | `/settings`, `/help` | Head / Both | Not yet built out beyond stubs |

**Modals:** `NewCaseModal.jsx` (head, multi-select investigators), `CaseDetailModal.jsx` (read-only case info, shared by both roles), `UploadCaseFilesModal.jsx` (investigator, first-time file upload).

**Shared components:** `Sidebar.jsx`, `TopBar.jsx` (includes the real notification bell dropdown), `CaseActionsMenu.jsx` (head-only three-dot menu — Start Investigation / Add Investigator / Edit, **UI only, not wired yet**).

**`utils/auth.js`** — `setUser()`/`getUser()` store the full login response in `localStorage` under `forensync_user`. `isOrgHead()` reads `role` from it.

---

## 7. Full End-to-End Flow (as it works right now)

```
1. Head logs in → creates a case (name, description, incident dates,
   multi-select investigators from real org data)
   → INSERT cases, INSERT case_investigators (status='pending') per investigator,
     INSERT notifications per investigator, INSERT activity_log row

2. Investigator logs in → sees the case under "Pending Assignments"
   (unread notifications) → clicks Confirm
   → UPDATE case_investigators.status = 'confirmed'
   → UPDATE notifications.is_read = true
   → INSERT activity_log row
   → Case now appears in their "Active Cases"

3. Investigator opens the case → clicks Upload (first time) →
   sees read-only case info → uploads log files (required) +
   other files (optional) → Continue
   → Files go to Supabase Storage bucket 'case-files'
   → INSERT case_files rows (one per file)
   → Redirects to CaseFilesPage

4. On CaseFilesPage → investigator clicks "Match Parsers"
   → Backend downloads each log file's bytes, runs detect_format()
     against the org's ADDED plugins only, returns ranked matches
   → Investigator can override any match via dropdown

5. Investigator clicks "Parse Log Files" (disabled until every
   file has a matched parser)
   → Backend downloads each file, calls get_plugin(name).parse(),
     inserts resulting events into the `events` table
   → Confirmation shown: "Parsed X files — Y events extracted"

6. Investigator can leave and come back — CaseFilesPage checks
   the `events` table on load and restores the Matched Parsers /
   Parse confirmation UI automatically (no re-parsing needed)
```

---

## 9. Timeline Generation & Event Correlation Status

### ✅ COMPLETED

The timeline generation feature has been implemented with the following functionality:

**Backend Infrastructure:**
- `Backend/routes/timeline.py` — Three endpoints:
  - `POST /api/v1/cases/{case_id}/timeline/generate` — Correlates events into sessions
  - `GET /api/v1/cases/{case_id}/timeline` — Retrieves timeline with optional filtering
  - `GET /api/v1/cases/{case_id}/timeline/stats` — Returns summary statistics

- `Backend/services/timeline_correlation_service.py` — Core correlation logic:
  - Chronological sorting (timestamped events first, NULL timestamps last)
  - Session correlation algorithm using actor + host + 30-minute rolling time window
  - Deterministic session ID generation (`{case_id}-S0000`, `{case_id}-S0001`, etc.)
  - Idempotent generation (safe to re-run)
  - Session persistence to database

**Database:**
- `timeline_events` table with `session_id` column (populated during timeline generation)
- Session IDs persist across re-runs

**Test Suite:**
- `Backend/tests/test_timeline_correlation.py` — 15 comprehensive tests covering:
  - ✅ Chronological ordering
  - ✅ Same actor+host within window → same session
  - ✅ Beyond 30-minute window → new session
  - ✅ Different actors → different sessions
  - ✅ Different hosts → different sessions
  - ✅ Deterministic session IDs across re-runs
  - ✅ Idempotent generation
  - ✅ Timeline retrieval with filtering (by actor, host)
  - ✅ Statistics endpoint
  - ✅ Error handling (case not found, unparsed files, no events)

**Test Results:** 43 passed, **1 failing**

### ⚠️ FAILING TEST

**Test:** `test_null_timestamps_handled_correctly`
**Location:** `Backend/tests/test_timeline_correlation.py:317-367`
**Status:** FAILING

**Expected Behavior:**
All events with NULL timestamps should be grouped into a **single** "UNKNOWN" session:
- 1 timestamped event → creates `{case_id}-S0000` session
- 2 NULL timestamp events → both should be in `{case_id}-UNKNOWN` session
- **Expected total sessions: 2**

**Actual Behavior:**
Each NULL timestamp event is creating its own session:
- 1 timestamped event → `{case_id}-S0000`
- NULL event 1 → `{case_id}-UNKNOWN` (or separate session)
- NULL event 2 → Another separate session
- **Actual total sessions: 3**

**Root Cause:**
In `Backend/services/timeline_correlation_service.py`, the `_correlate_events()` function around lines 267-289. The logic for handling NULL timestamp events needs to ensure ALL NULL events are added to the same UNKNOWN session, not creating multiple UNKNOWN sessions.

**Current Code Flow (Lines 267-289):**
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

**The Problem:**
When processing NULL timestamp events, the code checks if there's a `current_session` with `is_null_session=True`. However, after appending the NULL session to the `sessions` list, it creates a NEW session each time it encounters a NULL event after processing timestamped events. This breaks the "single UNKNOWN session for all NULL events" requirement.

**Fix Required:**
The logic needs to be modified to:
1. Check if a NULL session already exists in the `sessions` list (not just `current_session`)
2. If yes, append to that existing NULL session
3. If no, create the UNKNOWN session only once and reuse it for all subsequent NULL events

**Test Assertion (Line 351):**
```python
assert data["sessionCount"] == 2  # One for timestamped, one UNKNOWN for both NULL
```

**To Fix:**
Modify `_correlate_events()` to track whether an UNKNOWN session has been created and always add NULL timestamp events to that session rather than checking only the `current_session`.

### 🎯 WHAT'S NEXT

**For the next developer:**

1. **Fix the failing test** — Update `_correlate_events()` in `timeline_correlation_service.py` to properly group all NULL timestamp events into a single UNKNOWN session

2. **Run the test suite** to verify the fix:
   ```bash
   cd Backend
   python -m pytest tests/test_timeline_correlation.py -v
   ```

3. **Frontend Timeline View** — The backend is ready, but there's no UI yet to:
   - Display the timeline visually (chronological list, graph, etc.)
   - Show session groupings
   - Provide filtering controls (actor, host, source, action)
   - Display statistics

4. **Integration with Case Files Page** — Add a "Generate Timeline" button to `CaseFilesPage.jsx` that appears after parsing is complete

5. **Timeline Route & Component** — Create `Timeline.jsx` and add route `/cases/:caseId/timeline`

## 10. Known, Documented Limitations (for the report)

- Timezone assumed based on what's in the log; auth_log/linux_syslog rely on `incident_from`'s year as `starting_year`, no automatic timezone detection
- Clock skew between hosts not automatically detected (acknowledged open problem in the field, not just this project)
- Regex/detection plugins validated against specific real-world datasets — significantly different format variants may fall to `unparsed_event`
- Apache vs. Nginx access logs are structurally identical — detection cannot distinguish them, manual selection required
- 50MB file upload limit — hard Supabase Free tier platform cap, not a code limitation
- `events` table treated as regenerable, not permanent evidence — only raw files (Storage) and eventual timeline/insights output are meant to be the lasting record
