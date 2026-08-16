"""
routes/cases.py — Cases Blueprint.

Endpoints:
    GET  /api/v1/cases            — List all cases for the org.
    POST /api/v1/cases            — Create a new case.
    GET  /api/v1/cases/<case_id>  — Get a single case by ID.
    GET  /api/v1/activity         — Recent activity feed for the dashboard.

Case object shape (matches updated frontend mockData.js mockCases):
    {
        "caseId":            "CASE-1042",
        "name":              "...",
        "priority":          "High Priority" | "Medium Priority" | "Low Priority" | "Critical",
        "priorityColor":     "text-red-400" | "text-amber" | "text-blue-400",
        "investigators":     ["VK", "RS"],      ← initials array
        "extraInvestigators": 2,
        "lastUpdated":       "YYYY-MM-DD\nHH:MM",
        "status":            "Active" | "Pending" | "Closed"
    }

NOTE: The old shape used "timeframe", "lastModified", and "action" fields.
      Those were removed in the frontend update. The new shape uses "priority",
      "priorityColor", "investigators" (initials), "extraInvestigators",
      and "lastUpdated".  Status values changed: "Under Review" → "Pending".
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from services.case_service import (
    create_case as create_case_service,
    list_cases_for_investigator,
    list_cases_for_head,
)
from services.auth_service import NotFoundError, ServiceError
from services.activity_service import list_recent_activity
from services.file_service import upload_case_files
# from services.case_service import create_case as create_case_service
# from services.auth_service import NotFoundError, ServiceError


cases_bp = Blueprint("cases", __name__)


# ── In-memory stub store (mirrors updated mockData.js mockCases) ─────────── #
# TODO (database phase): delete this list and replace every reference with
#     CaseService.list(org_id=...), CaseService.get(case_id=...), etc.
_MOCK_CASES: list[dict] = [
    {
        "caseId":             "CASE-1042",
        "name":               "Organization Info Leak",
        "priority":           "High Priority",
        "priorityColor":      "text-red-400",
        "investigators":      ["VK", "RS"],
        "extraInvestigators": 2,
        "lastUpdated":        "2026-07-09\n18:22",
        "status":             "Active",
    },
    {
        "caseId":             "CASE-1041",
        "name":               "Unauthorized SSH Access",
        "priority":           "Medium Priority",
        "priorityColor":      "text-amber",
        "investigators":      ["AP", "NK"],
        "extraInvestigators": 1,
        "lastUpdated":        "2026-07-08\n16:45",
        "status":             "Active",
    },
    {
        "caseId":             "CASE-1040",
        "name":               "Data Exfiltration Attempt",
        "priority":           "Critical",
        "priorityColor":      "text-red-400",
        "investigators":      ["SM", "RP", "VK"],
        "extraInvestigators": 2,
        "lastUpdated":        "2026-07-08\n11:30",
        "status":             "Active",
    },
    {
        "caseId":             "CASE-1039",
        "name":               "Malware Infection — Endpoint",
        "priority":           "Medium Priority",
        "priorityColor":      "text-amber",
        "investigators":      ["AR", "PS"],
        "extraInvestigators": 0,
        "lastUpdated":        "2026-07-07\n10:15",
        "status":             "Pending",
    },
    {
        "caseId":             "CASE-1038",
        "name":               "Phishing Email Investigation",
        "priority":           "Low Priority",
        "priorityColor":      "text-blue-400",
        "investigators":      ["JD", "VK"],
        "extraInvestigators": 0,
        "lastUpdated":        "2026-07-06\n09:50",
        "status":             "Pending",
    },
]

# ── Recent activity feed (mirrors updated mockData.js recentActivity) ─────── #
# TODO (database phase): replace with ActivityService.list(org_id=..., limit=10)
_MOCK_ACTIVITY: list[dict] = [
    {
        "icon":      "✓",
        "iconColor": "text-teal bg-teal/10",
        "text":      "Case CASE-1042 logs converted successfully",
        "time":      "10 mins ago",
    },
    {
        "icon":      "↑",
        "iconColor": "text-amber bg-amber/10",
        "text":      "Evidence uploaded to CASE-1041",
        "time":      "25 mins ago",
    },
    {
        "icon":      "👤",
        "iconColor": "text-purple-400 bg-purple-400/10",
        "text":      "New investigator Rahul Sharma added to CASE-1040",
        "time":      "1 hour ago",
    },
    {
        "icon":      "📄",
        "iconColor": "text-blue-400 bg-blue-400/10",
        "text":      "Report generated for CASE-1037",
        "time":      "2 hours ago",
    },
]


# ── GET /api/v1/cases ───────────────────────────────────────────────────── #

# @cases_bp.get("/cases")
# def list_cases():
#     """
#     Return all cases for the authenticated organization.

#     Supports optional ?status= query parameter for filtering:
#         /api/v1/cases?status=Active
#         /api/v1/cases?status=Pending
#         /api/v1/cases?status=Closed

#     TODO (database phase):
#         Replace stub data with:
#             org_id = get_current_user_org()
#             status = request.args.get("status")
#             cases  = CaseService.list(org_id=org_id, status=status)
#             return success_response(data={"cases": [c.to_dict() for c in cases],
#                                           "total": len(cases)})

#     Response (200):
#         {
#             "status":  "success",
#             "message": "OK",
#             "data": {
#                 "cases": [ { ...case objects... } ],
#                 "total": 5
#             }
#         }
#     """
#     status_filter = request.args.get("status", "").strip()

#     if status_filter and status_filter != "All":
#         # TODO (database phase): pass status to CaseService.list(status=status_filter)
#         filtered = [c for c in _MOCK_CASES if c["status"] == status_filter]
#     else:
#         filtered = _MOCK_CASES

#     current_app.logger.debug(
#         "GET /cases  filter=%s  returning=%d", status_filter or "All", len(filtered)
#     )
#     return success_response(
#         data={"cases": filtered, "total": len(filtered)},
#     )


@cases_bp.get("/cases")
def list_cases():
    org_id = request.args.get("orgId", "").strip()
    user_id = request.args.get("userId", "").strip()
    role = request.args.get("role", "").strip().lower()

    if not org_id or not user_id:
        return error_response("orgId and userId are required.", 400, "Bad Request")

    try:
        cases = list_cases_for_head(org_id, user_id) if role == "head" else list_cases_for_investigator(org_id, user_id)
        return success_response(data={"cases": cases, "total": len(cases)})
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("List cases error: %s", e)
        return error_response("Failed to fetch cases.", 500, "Internal Server Error")
# def list_cases():

#     org_id = request.args.get("orgId", "").strip()
#     user_id = request.args.get("userId", "").strip()

#     if not org_id or not user_id:
#         return error_response(
#             "orgId and userId are required.",
#             400,
#             "Bad Request",
#         )

#     try:
#         cases = list_cases_for_investigator(org_id, user_id)

#         return success_response(
#             data={
#                 "cases": cases,
#                 "total": len(cases)
#             }
#         )

#     except NotFoundError as e:
#         return error_response(str(e), 404, "Not Found")

#     except ServiceError as e:
#         current_app.logger.error("List cases error: %s", e)
#         return error_response(
#             "Failed to fetch cases.",
#             500,
#             "Internal Server Error"
#         )


# ── POST /api/v1/cases ──────────────────────────────────────────────────── #

# @cases_bp.post("/cases")
# def create_case():
#     """
#     Create a new case.

#     Accepts either:
#         - multipart/form-data  (when log files are attached)
#         - application/json     (when creating a case without files)

#     Fields:
#         name        (required) — case name
#         description (optional) — incident summary
#         from        (optional) — incident start date  YYYY-MM-DD
#         to          (optional) — incident end date    YYYY-MM-DD
#         priority    (optional) — "High Priority" | "Medium Priority" |
#                                   "Low Priority" | "Critical"
#         files[]     (optional) — log files (multipart only)

#     TODO (database phase):
#         case = CaseService.create(name=name, description=description,
#                                   date_from=date_from, date_to=date_to,
#                                   priority=priority,
#                                   org_id=get_current_user_org())
#         return success_response(data=case.to_dict(), status_code=201)

#     TODO (parser phase):
#         for file in uploaded_files:
#             saved_path = FileService.save(file, case.id)
#             ParserJobService.enqueue(case_id=case.id, filepath=saved_path)

#     Response (201): new case object
#     """
#     content_type = request.content_type or ""
#     is_multipart = "multipart/form-data" in content_type

#     if is_multipart:
#         name        = (request.form.get("name")        or "").strip()
#         description = (request.form.get("description") or "").strip()
#         date_from   = (request.form.get("from")        or "").strip()
#         date_to     = (request.form.get("to")          or "").strip()
#         priority    = (request.form.get("priority")    or "Medium Priority").strip()
#     else:
#         body        = request.get_json(silent=True) or {}
#         name        = (body.get("name")        or "").strip()
#         description = (body.get("description") or "").strip()
#         date_from   = (body.get("from")        or "").strip()
#         date_to     = (body.get("to")          or "").strip()
#         priority    = (body.get("priority")    or "Medium Priority").strip()

#     if not name:
#         return error_response(
#             message="Case name is required.",
#             status_code=400,
#             error="Bad Request",
#             errors=[{"field": "name", "message": "This field is required."}],
#         )

#     current_app.logger.info(
#         "POST /cases (stub)  name=%s  priority=%s", name, priority
#     )

#     # Map priority to color (mirrors frontend logic)
#     priority_color_map = {
#         "Critical":         "text-red-400",
#         "High Priority":    "text-red-400",
#         "Medium Priority":  "text-amber",
#         "Low Priority":     "text-blue-400",
#     }

#     # TODO (database phase): replace with real DB insert and generated caseId
#     new_case = {
#         "caseId":             "CASE-1099",
#         "name":               name,
#         "description":        description,
#         "priority":           priority,
#         "priorityColor":      priority_color_map.get(priority, "text-ash"),
#         "investigators":      [],
#         "extraInvestigators": 0,
#         "lastUpdated":        "just now",
#         "status":             "Active",
#     }
#     return success_response(
#         data=new_case,
#         message="Case created successfully.",
#         status_code=201,
#     )

from services.case_service import create_case as create_case_service
from services.auth_service import NotFoundError, ServiceError

@cases_bp.post("/cases")
def create_case():
    body = request.get_json(silent=True) or {}

    name = (body.get("name") or "").strip()
    description = (body.get("description") or "").strip()
    date_from = (body.get("from") or "").strip()
    date_to = (body.get("to") or "").strip()
    priority = (body.get("priority") or "Medium Priority").strip()
    org_id = (body.get("orgId") or "").strip()
    created_by = (body.get("createdBy") or "").strip()
    investigator_ids = body.get("investigatorIds") or []

    if not name or not org_id or not created_by or not investigator_ids:
        return error_response(
            "name, orgId, createdBy, and at least one investigatorId are required.",
            400, "Bad Request",
        )

    try:
        new_case = create_case_service(
            org_id=org_id, created_by_user_id=created_by, name=name,
            description=description, priority=priority,
            incident_from=date_from, incident_to=date_to,
            investigator_ids=investigator_ids,
        )
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Create case error: %s", e)
        return error_response("Failed to create case.", 500, "Internal Server Error")

    return success_response(data=new_case, message="Case created successfully.", status_code=201)


# ── GET /api/v1/cases/<case_id> ─────────────────────────────────────────── #

from services.case_service import get_case_detail

@cases_bp.get("/cases/<string:case_id>")
def get_case(case_id: str):
    org_id = request.args.get("orgId", "").strip()
    if not org_id:
        return error_response("orgId query parameter is required.", 400, "Bad Request")

    try:
        case = get_case_detail(org_id, case_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Get case detail error: %s", e)
        return error_response("Failed to fetch case.", 500, "Internal Server Error")

    return success_response(data={"case": case})



# ── GET /api/v1/activity ────────────────────────────────────────────────── #

@cases_bp.get("/activity")
def get_activity():
    org_id = request.args.get("orgId", "").strip()
    limit = int(request.args.get("limit", 10))

    if not org_id:
        return error_response("orgId query parameter is required.", 400, "Bad Request")

    try:
        activity = list_recent_activity(org_id, limit=limit)
    except ServiceError as e:
        current_app.logger.error("List activity error: %s", e)
        return error_response("Failed to fetch activity.", 500, "Internal Server Error")

    return success_response(data={"activity": activity})
    # return success_response(
    #     data={"activity": _MOCK_ACTIVITY},
    # )
    
    cases_result = (
        sb.table("cases")
        .select("*")
        .in_("id", case_uuids)
        .execute()
    )

    cases = []

    for case in (cases_result.data or []):

        cases.append({
            "caseId": case["case_id"],
            "name": case["name"],
            "priority": case.get("priority", "Medium Priority"),
            "priorityColor": PRIORITY_COLOR_MAP.get(
                case.get("priority"),
                "text-ash"
            ),
            "investigators": [],
            "extraInvestigators": 0,
            "lastUpdated": case["updated_at"],
            "status": case["status"],
        })

    return cases

@cases_bp.post("/cases/<string:case_id>/files")
def upload_files(case_id: str):
    org_id = (request.form.get("orgId") or "").strip()
    user_id = (request.form.get("userId") or "").strip()

    if not org_id or not user_id:
        return error_response("orgId and userId are required.", 400, "Bad Request")

    log_files_raw = request.files.getlist("log_files")
    other_files_raw = request.files.getlist("other_files")

    if not log_files_raw:
        return error_response("At least one log file is required.", 400, "Bad Request")

    log_files = [(f.filename, f.read(), f.content_type) for f in log_files_raw if f.filename]
    other_files = [(f.filename, f.read(), f.content_type) for f in other_files_raw if f.filename]

    try:
        result = upload_case_files(org_id, case_id, user_id, log_files, other_files)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Upload files error: %s", e)
        return error_response("Failed to upload files.", 500, "Internal Server Error")

    return success_response(data=result, message="Files uploaded successfully.", status_code=201)

from services.file_service import upload_case_files, list_case_files

@cases_bp.get("/cases/<string:case_id>/files")
def get_case_files(case_id: str):
    org_id = request.args.get("orgId", "").strip()
    category = request.args.get("category", "").strip()

    if not org_id:
        return error_response("orgId query parameter is required.", 400, "Bad Request")

    try:
        files = list_case_files(org_id, case_id, category=category or None)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("List case files error: %s", e)
        return error_response("Failed to fetch files.", 500, "Internal Server Error")

    return success_response(data={"files": files, "total": len(files)})