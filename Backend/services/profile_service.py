"""
services/profile_service.py — Head/Org profile editing for ForenSync.
"""
import logging
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError

logger = logging.getLogger(__name__)


def update_profile(org_id: str, head_user_id: str, org_name: str, head_name: str) -> dict:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        head_result = (
            sb.table("users").select("id").eq("org_id", org_uuid)
            .eq("user_id", head_user_id).eq("role", "head").execute()
        )
        if not head_result.data:
            raise NotFoundError("Head not found in this organization.")
        head_uuid = head_result.data[0]["id"]

        sb.table("organizations").update({"name": org_name}).eq("id", org_uuid).execute()
        sb.table("users").update({"name": head_name}).eq("id", head_uuid).execute()

        logger.info("[PROFILE] Updated  org_id=%s  head_id=%s", org_id, head_user_id)
        return {"orgName": org_name, "headName": head_name}

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def get_org_settings(org_id: str) -> dict:
    sb = _get_client()
    try:
        result = sb.table("organizations").select("default_priority, default_correlation_window").eq("org_id", org_id).execute()
        if not result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        row = result.data[0]
        return {
            "defaultPriority": row.get("default_priority") or "Medium Priority",
            "defaultCorrelationWindow": row.get("default_correlation_window") or 30,
        }
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def update_org_settings(org_id: str, default_priority: str, default_correlation_window: int) -> dict:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        sb.table("organizations").update({
            "default_priority": default_priority,
            "default_correlation_window": default_correlation_window,
        }).eq("id", org_uuid).execute()

        return {"defaultPriority": default_priority, "defaultCorrelationWindow": default_correlation_window}
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")