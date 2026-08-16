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