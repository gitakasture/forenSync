"""
routes/cases.py — Cases Blueprint.

Endpoints:
    GET  /api/v1/cases            — List all cases for the org.
    POST /api/v1/cases            — Create a new case + attach log files.
    GET  /api/v1/cases/<case_id>  — Get a single case by ID.

Mock data matches mockData.js exactly so the Dashboard renders correctly
the moment the frontend swaps mockCases for a real API call.

Case object shape (matches frontend mockData.js mockCases):
    {
        "caseId":       "CASE-1042",
        "name":         "...",
        "timeframe":    "DD Mon – DD Mon YYYY",
        "lastModified": "YYYY-MM-DD HH:MM",
        "status":       "Active" | "Under Review" | "Closed",
        "action":       "Open"   | "View"
    }
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from utils.validators import require_json_fields, require_form_fields

cases_bp = Blueprint("cases", __name__)


# ── In-memory stub store (mirrors mockData.js mockCases) ────────────────── #
# TODO (database phase): delete this list and replace every reference with
#     CaseService.list(org_id=...), CaseService.get(case_id=...), etc.
_MOCK_CASES: list[dict] = [
    {
        "caseId":       "CASE-1042",
        "name":         "Unauthorized SSH Access — prod-web-03",
        "timeframe":    "02 Jul – 05 Jul 2026",
        "lastModified": "2026-07-09 18:22",
        "status":       "Active",
        "action":       "Open",
    },
    {
        "caseId":       "CASE-1041",
        "name":         "Suspicious Apache Traffic Spike",
        "timeframe":    "28 Jun – 30 Jun 2026",
        "lastModified": "2026-07-08 11:05",
        "status":       "Under Review",
        "action":       "Open",
    },
    {
        "caseId":       "CASE-1038",
        "name":         "Failed Login Brute Force — auth-gateway",
        "timeframe":    "18 Jun – 20 Jun 2026",
        "lastModified": "2026-07-02 09:40",
        "status":       "Active",
        "action":       "Open",
    },
    {
        "caseId":       "CASE-1031",
        "name":         "Data Exfiltration Attempt — file-srv-01",
        "timeframe":    "01 Jun – 04 Jun 2026",
        "lastModified": "2026-06-25 16:12",
        "status":       "Closed",
        "action":       "View",
    },
    {
        "caseId":       "CASE-1027",
        "name":         "Privilege Escalation — internal CI runner",
        "timeframe":    "14 May – 16 May 2026",
        "lastModified": "2026-06-10 08:55",
        "status":       "Closed",
        "action":       "View",
    },
]


# ── GET /api/v1/cases ───────────────────────────────────────────────────── #

@cases_bp.get("/cases")
def list_cases():
    """
    Return all cases for the authenticated organization.

    TODO (database phase):
        Replace stub data with:
            org_id = get_current_user_org()   # from session / JWT
            cases  = CaseService.list(org_id=org_id)
            return success_response(data={"cases": [c.to_dict() for c in cases], "total": len(cases)})

    Response (200):
        {
            "status":  "success",
            "message": "OK",
            "data": {
                "cases": [ { ...case objects... } ],
                "total": 5
            }
        }
    """
    current_app.logger.debug("GET /cases — returning %d stub cases", len(_MOCK_CASES))
    return success_response(
        data={"cases": _MOCK_CASES, "total": len(_MOCK_CASES)},
    )


# ── POST /api/v1/cases ──────────────────────────────────────────────────── #

@cases_bp.post("/cases")
def create_case():
    """
    Create a new case.

    Accepts either:
        - multipart/form-data  (when log files are attached)
        - application/json     (when creating a case without files)

    Fields:
        name        (required) — case name
        description (optional) — incident summary
        from        (optional) — incident start date  YYYY-MM-DD
        to          (optional) — incident end date    YYYY-MM-DD
        files[]     (optional) — one or more log files (multipart only)

    TODO (database phase):
        Replace stub return with:
            case = CaseService.create(
                name=name, description=description,
                date_from=date_from, date_to=date_to,
                org_id=get_current_user_org(),
            )
            return success_response(data=case.to_dict(), status_code=201)

    TODO (parser phase):
        After saving the case, dispatch each attached file:
            for file in uploaded_files:
                saved_path = FileService.save(file, case.id)
                ParserJobService.enqueue(case_id=case.id, filepath=saved_path)

    Response (201):
        {
            "status":  "success",
            "message": "Case created successfully.",
            "data":    { ...case object... }
        }
    """
    # Support both multipart/form-data and application/json
    content_type = request.content_type or ""
    is_multipart = "multipart/form-data" in content_type

    if is_multipart:
        name        = (request.form.get("name")        or "").strip()
        description = (request.form.get("description") or "").strip()
        date_from   = (request.form.get("from")        or "").strip()
        date_to     = (request.form.get("to")          or "").strip()
    else:
        body        = request.get_json(silent=True) or {}
        name        = (body.get("name")        or "").strip()
        description = (body.get("description") or "").strip()
        date_from   = (body.get("from")        or "").strip()
        date_to     = (body.get("to")          or "").strip()

    if not name:
        return error_response(
            message="Case name is required.",
            status_code=400,
            error="Bad Request",
            errors=[{"field": "name", "message": "This field is required."}],
        )

    current_app.logger.info("POST /cases (stub)  name=%s  from=%s  to=%s", name, date_from, date_to)

    # Build human-readable timeframe string for the frontend table
    timeframe = "—"
    if date_from or date_to:
        timeframe = f"{date_from or '?'} – {date_to or '?'}"

    # ── Stub response — replace with real DB insert ───────────────────── #
    new_case = {
        "caseId":       "CASE-1099",   # TODO: generated by DB sequence
        "name":         name,
        "description":  description,
        "timeframe":    timeframe,
        "lastModified": "just now",
        "status":       "Active",
        "action":       "Open",
    }
    return success_response(
        data=new_case,
        message="Case created successfully.",
        status_code=201,
    )


# ── GET /api/v1/cases/<case_id> ─────────────────────────────────────────── #

@cases_bp.get("/cases/<string:case_id>")
def get_case(case_id: str):
    """
    Return a single case by ID.

    TODO (database phase):
        Replace stub lookup with:
            case = CaseService.get(case_id)
            if not case:
                return error_response(f"Case '{case_id}' not found.", 404, error="Not Found")
            return success_response(data={"case": case.to_dict()})

    Response (200): { "data": { "case": { ...case object... } } }
    Response (404): if case_id is not found
    """
    # TODO (database phase): replace with CaseService.get(case_id)
    case = next((c for c in _MOCK_CASES if c["caseId"] == case_id), None)
    if not case:
        return error_response(
            message=f"Case '{case_id}' not found.",
            status_code=404,
            error="Not Found",
        )

    current_app.logger.debug("GET /cases/%s — found", case_id)
    return success_response(data={"case": case})
