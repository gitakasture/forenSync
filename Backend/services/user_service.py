"""
services/user_service.py — User listing service for ForenSync.

Provides organization-scoped user queries against Supabase.
Reuses the same cached Supabase client as auth_service.
"""

import logging
from services.auth_service import _get_client, NotFoundError, ServiceError
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)


def list_users(org_id: str, role: str = None, status: str = None, search: str = None) -> list[dict]:
    """
    List users belonging to an organization, with optional filters.

    Args:
        org_id: e.g. "ORG-4410" (text ID, not the uuid)
        role:   "investigator" | "head" (optional)
        status: "Active" | "Inactive" (optional)
        search: matches against name or user_id (optional)

    Returns:
        list of dicts matching the UsersTeams.jsx mockUsers shape:
        { initials, name, id, role, cases, status }

    Raises:
        NotFoundError: org_id doesn't exist
        ServiceError:  Supabase API error
    """
    sb = _get_client()

    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
    except APIError as e:
        logger.error("[USERS] Org lookup failed: %s", e)
        raise ServiceError(f"Database error during org lookup: {e.message}")

    if not org_result.data:
        raise NotFoundError(f"Organization '{org_id}' not found.")

    org_uuid = org_result.data[0]["id"]

    try:
        query = sb.table("users").select("user_id, name, role, status").eq("org_id", org_uuid)
        if role:
            query = query.eq("role", role)
        if status:
            query = query.eq("status", status)
        result = query.execute()
    except APIError as e:
        logger.error("[USERS] User query failed: %s", e)
        raise ServiceError(f"Database error during user lookup: {e.message}")

    rows = result.data or []

    if search:
        s = search.lower()
        rows = [r for r in rows if s in r["name"].lower() or s in r["user_id"].lower()]

    users = []
    for r in rows:
        initials = "".join(p[0].upper() for p in r["name"].split() if p)[:2]
        users.append({
            "initials": initials,
            "name": r["name"],
            "id": r["user_id"],
            "role": "Head of Team" if r["role"] == "head" else "Investigator",
            "cases": 0,  # TODO: wire real count once a cases table exists
            "status": r["status"],
        })

    logger.info("[USERS] org_id=%s role=%s returning=%d", org_id, role or "All", len(users))
    return users