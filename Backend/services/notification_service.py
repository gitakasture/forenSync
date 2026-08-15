"""
services/notification_service.py — Notifications for ForenSync.
"""

import logging
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError
from services.activity_service import log_activity

logger = logging.getLogger(__name__)


def list_notifications(org_id: str, user_id: str) -> list[dict]:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        user_result = (
            sb.table("users").select("id").eq("org_id", org_uuid).eq("user_id", user_id).execute()
        )
        if not user_result.data:
            raise NotFoundError("User not found.")
        user_uuid = user_result.data[0]["id"]

        result = (
            sb.table("notifications")
            .select("id, text, is_read, related_case_id, created_at")
            .eq("user_id", user_uuid)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


# def confirm_case_assignment(org_id: str, user_id: str, notification_id: str) -> dict:
#     """
#     Marks the notification as read AND flips the related
#     case_investigators row to status='confirmed'.
#     """
#     sb = _get_client()
#     try:
#         org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
#         if not org_result.data:
#             raise NotFoundError(f"Organization '{org_id}' not found.")
#         org_uuid = org_result.data[0]["id"]

#         user_result = (
#             sb.table("users").select("id").eq("org_id", org_uuid).eq("user_id", user_id).execute()
#         )
#         if not user_result.data:
#             raise NotFoundError("User not found.")
#         user_uuid = user_result.data[0]["id"]

#         notif_result = (
#             sb.table("notifications")
#             .select("id, related_case_id, user_id")
#             .eq("id", notification_id)
#             .execute()
#         )
#         if not notif_result.data:
#             raise NotFoundError("Notification not found.")
#         notif = notif_result.data[0]

#         if notif["user_id"] != user_uuid:
#             raise NotFoundError("Notification does not belong to this user.")

#         case_uuid = notif["related_case_id"]
#         if case_uuid:
#             sb.table("case_investigators").update({"status": "confirmed"}) \
#                 .eq("case_id", case_uuid).eq("user_id", user_uuid).execute()

#         sb.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()

#         logger.info("[NOTIFICATIONS] Confirmed  user_id=%s  case_uuid=%s", user_id, case_uuid)
#         return {"confirmed": True, "caseId": case_uuid}

#     except APIError as e:
#         raise ServiceError(f"Database error: {e.message}")

def confirm_case_assignment(org_id: str, user_id: str, notification_id: str) -> dict:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        user_result = (
            sb.table("users").select("id, name").eq("org_id", org_uuid).eq("user_id", user_id).execute()
        )
        if not user_result.data:
            raise NotFoundError("User not found.")
        user_uuid = user_result.data[0]["id"]
        user_name = user_result.data[0]["name"]

        notif_result = (
            sb.table("notifications").select("id, related_case_id, user_id").eq("id", notification_id).execute()
        )
        if not notif_result.data:
            raise NotFoundError("Notification not found.")
        notif = notif_result.data[0]

        if notif["user_id"] != user_uuid:
            raise NotFoundError("Notification does not belong to this user.")

        case_uuid = notif["related_case_id"]
        case_text_id = None
        if case_uuid:
            sb.table("case_investigators").update({"status": "confirmed"}) \
                .eq("case_id", case_uuid).eq("user_id", user_uuid).execute()

            case_lookup = sb.table("cases").select("case_id").eq("id", case_uuid).execute()
            if case_lookup.data:
                case_text_id = case_lookup.data[0]["case_id"]

        sb.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()

        if case_uuid and case_text_id:
            log_activity(
                sb, org_uuid, user_uuid, "investigator_confirmed",
                f"{user_name} confirmed assignment to {case_text_id}",
                related_case_id=case_uuid,
            )

        logger.info("[NOTIFICATIONS] Confirmed  user_id=%s  case_uuid=%s", user_id, case_uuid)
        return {"confirmed": True, "caseId": case_uuid}

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")