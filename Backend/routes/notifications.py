"""
routes/notifications.py — Notifications Blueprint.

Endpoints:
    GET  /api/v1/notifications?orgId=...&userId=...
    POST /api/v1/notifications/<notification_id>/confirm   { orgId, userId }
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from services.notification_service import list_notifications, confirm_case_assignment
from services.auth_service import NotFoundError, ServiceError

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/notifications")
def get_notifications():
    org_id = request.args.get("orgId", "").strip()
    user_id = request.args.get("userId", "").strip()

    if not org_id or not user_id:
        return error_response("orgId and userId query parameters are required.", 400, "Bad Request")

    try:
        notifications = list_notifications(org_id, user_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("List notifications error: %s", e)
        return error_response("Failed to fetch notifications.", 500, "Internal Server Error")

    return success_response(data={"notifications": notifications, "total": len(notifications)})


@notifications_bp.post("/notifications/<string:notification_id>/confirm")
def confirm_notification(notification_id: str):
    body = request.get_json(silent=True) or {}
    org_id = (body.get("orgId") or "").strip()
    user_id = (body.get("userId") or "").strip()

    if not org_id or not user_id:
        return error_response("orgId and userId are required.", 400, "Bad Request")

    try:
        result = confirm_case_assignment(org_id, user_id, notification_id)
    except NotFoundError as e:
        return error_response(str(e), 404, "Not Found")
    except ServiceError as e:
        current_app.logger.error("Confirm notification error: %s", e)
        return error_response("Failed to confirm assignment.", 500, "Internal Server Error")

    return success_response(data=result, message="Case assignment confirmed.")