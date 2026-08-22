"""
services/saved_view_service.py — Saved Timeline Views for ForenSync.
"""

import logging
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError

logger = logging.getLogger(__name__)


def _resolve_case_and_user(sb, org_id: str, case_id: str, user_id: str):
    org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
    if not org_result.data:
        raise NotFoundError(f"Organization '{org_id}' not found.")
    org_uuid = org_result.data[0]["id"]

    case_result = sb.table("cases").select("id").eq("org_id", org_uuid).eq("case_id", case_id).execute()
    if not case_result.data:
        raise NotFoundError(f"Case '{case_id}' not found.")
    case_uuid = case_result.data[0]["id"]

    user_result = sb.table("users").select("id").eq("org_id", org_uuid).eq("user_id", user_id).execute()
    if not user_result.data:
        raise NotFoundError("User not found.")
    user_uuid = user_result.data[0]["id"]

    return case_uuid, user_uuid


def save_view(org_id: str, case_id: str, user_id: str, name: str, filters: dict, view_mode: str) -> dict:
    sb = _get_client()
    try:
        case_uuid, user_uuid = _resolve_case_and_user(sb, org_id, case_id, user_id)

        result = (
            sb.table("saved_views")
            .insert({
                "case_id": case_uuid,
                "user_id": user_uuid,
                "name": name,
                "filters": filters,
                "view_mode": view_mode,
            })
            .execute()
        )
        row = result.data[0]
        logger.info("[SAVED_VIEWS] Created  case_id=%s  user_id=%s  name=%s", case_id, user_id, name)
        return {"id": row["id"], "name": row["name"], "filters": row["filters"], "viewMode": row["view_mode"]}

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def list_views(org_id: str, case_id: str, user_id: str) -> list[dict]:
    sb = _get_client()
    try:
        case_uuid, user_uuid = _resolve_case_and_user(sb, org_id, case_id, user_id)

        result = (
            sb.table("saved_views")
            .select("id, name, filters, view_mode, created_at")
            .eq("case_id", case_uuid)
            .eq("user_id", user_uuid)
            .order("created_at", desc=True)
            .execute()
        )
        return [
            {"id": r["id"], "name": r["name"], "filters": r["filters"], "viewMode": r["view_mode"]}
            for r in (result.data or [])
        ]

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def delete_view(view_id: str, user_id: str, org_id: str) -> dict:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        user_result = sb.table("users").select("id").eq("org_id", org_uuid).eq("user_id", user_id).execute()
        if not user_result.data:
            raise NotFoundError("User not found.")
        user_uuid = user_result.data[0]["id"]

        view_result = sb.table("saved_views").select("id, user_id").eq("id", view_id).execute()
        if not view_result.data:
            raise NotFoundError("Saved view not found.")
        if view_result.data[0]["user_id"] != user_uuid:
            raise NotFoundError("This saved view does not belong to you.")

        sb.table("saved_views").delete().eq("id", view_id).execute()
        return {"deleted": True}

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")