"""
services/activity_service.py — Activity log for ForenSync.
"""

import logging
from datetime import datetime, timezone
from postgrest.exceptions import APIError
from services.auth_service import _get_client, ServiceError

logger = logging.getLogger(__name__)

ICON_MAP = {
    "case_created": ("📋", "text-blue-400 bg-blue-400/10"),
    "investigator_confirmed": ("👤", "text-purple-400 bg-purple-400/10"),
}


def log_activity(sb, org_uuid, actor_uuid, action_type, description, related_case_id=None):
    try:
        sb.table("activity_log").insert({
            "org_id": org_uuid,
            "actor_user_id": actor_uuid,
            "action_type": action_type,
            "description": description,
            "related_case_id": related_case_id,
        }).execute()
    except APIError as e:
        # Don't let activity logging break the actual primary action
        logger.error("[ACTIVITY] Failed to log activity: %s", e)


def _time_ago(created_at_raw: str) -> str:
    created = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
    seconds = int((datetime.now(timezone.utc) - created).total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} day{'s' if days != 1 else ''} ago"


def list_recent_activity(org_id: str, limit: int = 10) -> list[dict]:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise ServiceError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        result = (
            sb.table("activity_log")
            .select("action_type, description, created_at")
            .eq("org_id", org_uuid)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        activity = []
        for row in (result.data or []):
            icon, icon_color = ICON_MAP.get(row["action_type"], ("•", "text-ash bg-raised"))
            activity.append({
                "icon": icon,
                "iconColor": icon_color,
                "text": row["description"],
                "time": _time_ago(row["created_at"]),
            })
        return activity

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")