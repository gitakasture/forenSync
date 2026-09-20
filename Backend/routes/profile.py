"""
routes/profile.py — Head/Org profile editing Blueprint.
"""
from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from services.profile_service import update_profile
from services.profile_service import get_org_settings, update_org_settings
from services.auth_service import NotFoundError, ServiceError

profile_bp = Blueprint("profile", __name__)


@profile_bp.put("/profile")
def update_profile_route():
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    head_user_id = (body.get("headUserId") or "").strip()
    org_name = (body.get("orgName") or "").strip()
    head_name = (body.get("headName") or "").strip()

    if not org_id or not head_user_id or not org_name or not head_name:
        return error_response("orgId, headUserId, orgName, and headName are required.", 400, "Bad Request")

    try:
        result = update_profile(org_id, head_user_id, org_name, head_name)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Update profile error: %s", e)
        return error_response("Failed to update profile.", 500, "Internal Server Error")

    return success_response(data=result, message="Profile updated.")


@profile_bp.get("/organizations/settings")
def get_settings_route():
    org_id = request.args.get("orgId", "").strip()
    if not org_id:
        return error_response("orgId query parameter is required.", 400, "Bad Request")
    try:
        settings = get_org_settings(org_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        return error_response(str(e), 500, "Internal Server Error")
    return success_response(data=settings)


@profile_bp.put("/organizations/settings")
def update_settings_route():
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    default_priority = (body.get("defaultPriority") or "").strip()
    default_correlation_window = body.get("defaultCorrelationWindow")

    if not org_id or not default_priority or not default_correlation_window:
        return error_response("orgId, defaultPriority, and defaultCorrelationWindow are required.", 400, "Bad Request")

    try:
        result = update_org_settings(org_id, default_priority, int(default_correlation_window))
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        return error_response(str(e), 500, "Internal Server Error")

    return success_response(data=result, message="Settings updated.")