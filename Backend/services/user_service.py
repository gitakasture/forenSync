"""
services/user_service.py — User listing service for ForenSync.

Provides organization-scoped user queries against Supabase.
Reuses the same cached Supabase client as auth_service.
"""

import logging
from services.auth_service import _get_client, NotFoundError, ServiceError, ConflictError
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)


# def list_users(org_id: str, role: str = None, status: str = None, search: str = None) -> list[dict]:
#     """
#     List users belonging to an organization, with optional filters.

#     Args:
#         org_id: e.g. "ORG-4410" (text ID, not the uuid)
#         role:   "investigator" | "head" (optional)
#         status: "Active" | "Inactive" (optional)
#         search: matches against name or user_id (optional)

#     Returns:
#         list of dicts matching the UsersTeams.jsx mockUsers shape:
#         { initials, name, id, role, cases, status }

#     Raises:
#         NotFoundError: org_id doesn't exist
#         ServiceError:  Supabase API error
#     """
#     sb = _get_client()

#     try:
#         org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
#     except APIError as e:
#         logger.error("[USERS] Org lookup failed: %s", e)
#         raise ServiceError(f"Database error during org lookup: {e.message}")

#     if not org_result.data:
#         raise NotFoundError(f"Organization '{org_id}' not found.")

#     org_uuid = org_result.data[0]["id"]

#     try:
#         query = sb.table("users").select("user_id, name, role, status").eq("org_id", org_uuid)
#         if role:
#             query = query.eq("role", role)
#         if status:
#             query = query.eq("status", status)
#         result = query.execute()
#     except APIError as e:
#         logger.error("[USERS] User query failed: %s", e)
#         raise ServiceError(f"Database error during user lookup: {e.message}")

#     rows = result.data or []

#     if search:
#         s = search.lower()
#         rows = [r for r in rows if s in r["name"].lower() or s in r["user_id"].lower()]

#     users = []
#     for r in rows:
#         initials = "".join(p[0].upper() for p in r["name"].split() if p)[:2]
#         users.append({
#             "initials": initials,
#             "name": r["name"],
#             "id": r["user_id"],
#             "role": "Head of Team" if r["role"] == "head" else "Investigator",
#             "cases": 0,  # TODO: wire real count once a cases table exists
#             "status": r["status"],
#         })

#     logger.info("[USERS] org_id=%s role=%s returning=%d", org_id, role or "All", len(users))
#     return users



def list_users(org_id: str, role: str = None, status: str = None, search: str = None) -> list[dict]:
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
        query = sb.table("users").select("id, user_id, name, role, status").eq("org_id", org_uuid)
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

        case_count = 0
        try:
            count_result = (
                sb.table("case_investigators")
                .select("id", count="exact")
                .eq("user_id", r["id"])
                .eq("status", "confirmed")
                .execute()
            )
            case_count = count_result.count or 0
        except APIError:
            pass  # don't fail the whole list over one count lookup

        users.append({
            "initials": initials,
            "name": r["name"],
            "id": r["user_id"],
            "role": "Head of Team" if r["role"] == "head" else "Investigator",
            "cases": case_count,
            "status": r["status"],
        })

    logger.info("[USERS] org_id=%s role=%s returning=%d", org_id, role or "All", len(users))
    return users


def update_user_status(org_id: str, user_id: str, new_status: str) -> dict:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        user_result = sb.table("users").select("id").eq("org_id", org_uuid).eq("user_id", user_id).execute()
        if not user_result.data:
            raise NotFoundError(f"User '{user_id}' not found.")
        user_uuid = user_result.data[0]["id"]

        sb.table("users").update({"status": new_status}).eq("id", user_uuid).execute()
        logger.info("[USERS] Status updated  user_id=%s  new_status=%s", user_id, new_status)
        return {"id": user_id, "status": new_status}

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")
    

def add_investigator(org_id: str, investigator_id: str, investigator_name: str) -> dict:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        existing = sb.table("users").select("id").eq("org_id", org_uuid).eq("user_id", investigator_id).execute()
        if existing.data:
            raise ConflictError(f"Investigator ID '{investigator_id}' already exists in this organization.")

        result = sb.table("users").insert({
            "user_id": investigator_id,
            "name": investigator_name,
            "role": "investigator",
            "status": "Active",
            "org_id": org_uuid,
        }).execute()

        row = result.data[0]
        initials = "".join(p[0].upper() for p in row["name"].split() if p)[:2]
        return {
            "initials": initials,
            "name": row["name"],
            "id": row["user_id"],
            "role": "Investigator",
            "cases": 0,
            "status": row["status"],
        }
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")