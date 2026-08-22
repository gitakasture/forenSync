"""
routes/plugins.py — Parser Plugin marketplace Blueprint.
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from services.plugin_service import (
    list_plugins_for_org, add_plugin_to_org, remove_plugin_from_org, match_parsers_for_case,
)
from services.auth_service import NotFoundError, ServiceError
from services.parsing_service import parse_case_files
from services.parsing_service import get_parse_status_for_case
from services.timeline_service import generate_timeline, get_timeline
from services.saved_view_service import save_view, list_views, delete_view

plugins_bp = Blueprint("plugins", __name__)


@plugins_bp.get("/plugins")
def get_plugins():
    org_id = request.args.get("orgId", "").strip()
    if not org_id:
        return error_response("orgId query parameter is required.", 400, "Bad Request")
    try:
        plugins = list_plugins_for_org(org_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("List plugins error: %s", e)
        return error_response("Failed to fetch plugins.", 500, "Internal Server Error")
    return success_response(data={"plugins": plugins})


@plugins_bp.post("/plugins/<string:plugin_name>/add")
def add_plugin(plugin_name: str):
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    if not org_id:
        return error_response("orgId is required.", 400, "Bad Request")
    try:
        result = add_plugin_to_org(org_id, plugin_name)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Add plugin error: %s", e)
        return error_response("Failed to add plugin.", 500, "Internal Server Error")
    return success_response(data=result, message="Plugin added.")


@plugins_bp.post("/plugins/<string:plugin_name>/remove")
def remove_plugin(plugin_name: str):
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    if not org_id:
        return error_response("orgId is required.", 400, "Bad Request")
    try:
        result = remove_plugin_from_org(org_id, plugin_name)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Remove plugin error: %s", e)
        return error_response("Failed to remove plugin.", 500, "Internal Server Error")
    return success_response(data=result, message="Plugin removed.")


@plugins_bp.post("/cases/<string:case_id>/match-parsers")
def match_parsers(case_id: str):
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    if not org_id:
        return error_response("orgId is required.", 400, "Bad Request")
    try:
        results = match_parsers_for_case(org_id, case_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Match parsers error: %s", e)
        return error_response(str(e), 500, "Internal Server Error")
    return success_response(data={"results": results})



@plugins_bp.post("/cases/<string:case_id>/parse-files")
def parse_files(case_id: str):
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    matches = body.get("matches") or []

    if not org_id:
        return error_response("orgId is required.", 400, "Bad Request")
    if not matches or any(not m.get("pluginName") for m in matches):
        return error_response(
            "Every log file must have a matched parser before parsing.", 400, "Bad Request",
        )

    try:
        result = parse_case_files(org_id, case_id, matches)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Parse files error: %s", e)
        return error_response(str(e), 500, "Internal Server Error")

    return success_response(data=result, message="Files parsed successfully.")

@plugins_bp.get("/cases/<string:case_id>/parse-status")
def parse_status(case_id: str):
    org_id = request.args.get("orgId", "").strip()
    if not org_id:
        return error_response("orgId query parameter is required.", 400, "Bad Request")

    try:
        results = get_parse_status_for_case(org_id, case_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Parse status error: %s", e)
        return error_response("Failed to fetch parse status.", 500, "Internal Server Error")

    return success_response(data={"status": results})

@plugins_bp.post("/cases/<string:case_id>/generate-timeline")
def generate_timeline_route(case_id: str):
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    window_minutes = int(body.get("windowMinutes", 30))

    if not org_id:
        return error_response("orgId is required.", 400, "Bad Request")

    try:
        result = generate_timeline(org_id, case_id, window_minutes=window_minutes)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Generate timeline error: %s", e)
        return error_response(str(e), 500, "Internal Server Error")

    return success_response(data=result, message="Timeline generated.")


@plugins_bp.get("/cases/<string:case_id>/timeline")
def get_timeline_route(case_id: str):
    org_id = request.args.get("orgId", "").strip()
    if not org_id:
        return error_response("orgId query parameter is required.", 400, "Bad Request")

    filters = {
        "actor": request.args.get("actor", "").strip(),
        "host": request.args.get("host", "").strip(),
        "source": request.args.get("source", "").strip(),
        "action": request.args.get("action", "").strip(),
    }

    try:
        result = get_timeline(org_id, case_id, filters)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Get timeline error: %s", e)
        return error_response("Failed to fetch timeline.", 500, "Internal Server Error")

    return success_response(data=result)

@plugins_bp.post("/cases/<string:case_id>/saved-views")
def create_saved_view(case_id: str):
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    user_id = (body.get("userId") or "").strip()
    name = (body.get("name") or "").strip()
    filters = body.get("filters") or {}
    view_mode = (body.get("viewMode") or "table").strip()

    if not org_id or not user_id or not name:
        return error_response("orgId, userId, and name are required.", 400, "Bad Request")

    try:
        result = save_view(org_id, case_id, user_id, name, filters, view_mode)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        return error_response(str(e), 500, "Internal Server Error")

    return success_response(data=result, message="View saved.", status_code=201)


@plugins_bp.get("/cases/<string:case_id>/saved-views")
def get_saved_views(case_id: str):
    org_id = request.args.get("orgId", "").strip()
    user_id = request.args.get("userId", "").strip()

    if not org_id or not user_id:
        return error_response("orgId and userId query parameters are required.", 400, "Bad Request")

    try:
        views = list_views(org_id, case_id, user_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        return error_response(str(e), 500, "Internal Server Error")

    return success_response(data={"views": views})


@plugins_bp.delete("/saved-views/<string:view_id>")
def remove_saved_view(view_id: str):
    org_id = request.args.get("orgId", "").strip()
    user_id = request.args.get("userId", "").strip()

    if not org_id or not user_id:
        return error_response("orgId and userId query parameters are required.", 400, "Bad Request")

    try:
        result = delete_view(view_id, user_id, org_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        return error_response(str(e), 500, "Internal Server Error")

    return success_response(data=result, message="View deleted.")