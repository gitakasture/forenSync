"""
services/auth_service.py - Authentication service for ForenSync.

All Supabase database interactions for Register and Login live here.
Route handlers call these functions and receive plain dicts or raise
typed exceptions. No Flask request/response objects enter this module.

Live Supabase tables (confirmed from database inspection):
    organizations  columns: id (uuid), org_id (text), name (text),
                            is_active (bool), created_at (timestamptz)
    users          columns: id (uuid), user_id (text), name (text),
                            role (user_role enum), status (user_status enum),
                            org_id (uuid FK), created_at (timestamptz)

IMPORTANT: organizations.head_id does NOT exist in the live database.
The organization head is represented by a row in the users table with
role='head'. The backend must NOT insert head_id into organizations.

Supabase client:
    Uses the SERVICE ROLE key so the backend can read/write without a
    user JWT. The key is only used server-side and never sent to the browser.

TODO (future): Add bcrypt password hashing when schema gains a password column.
TODO (future): Replace SERVICE KEY with anon key + RLS once JWT auth is live.
"""

import os
import logging
from functools import lru_cache
from postgrest.exceptions import APIError
from supabase import create_client, Client

logger = logging.getLogger(__name__)


#  Supabase client singleton 

@lru_cache(maxsize=1)
def _get_client() -> Client:
    """
    Return a cached Supabase client instance.
    lru_cache(maxsize=1) ensures create_client() is called once per process.

    Raises:
        EnvironmentError: if SUPABASE_URL or SUPABASE_SERVICE_KEY are missing.
    """
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()

    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env. "
            "Get them from: Supabase Dashboard > Project Settings > API."
        )

    logger.debug("Supabase client initialised  url=%s", url)
    return create_client(url, key)


#  Register 

# def register_organization(
#     org_id: str,
#     org_name: str,
#     head_id: str,
#     investigators: list[dict],
# ) -> dict:
#     """
#     Register a new organization and its users in Supabase.

#     Database write order:
#         1. INSERT organizations (org_id, name)           -- no head_id column
#         2. INSERT users: head user  (user_id=head_id, role='head')
#         3. INSERT users: investigators (role='investigator')

#     Args:
#         org_id:        e.g. "ORG-4410"
#         org_name:      e.g. "Sentinel Cyber Forensics"
#         head_id:       e.g. "HEAD-0001"  (becomes a users row, NOT an org column)
#         investigators: list of { "name": str, "id": str }

#     Returns:
#         dict: { orgId, orgName, orgHeadId, investigators }

#     Raises:
#         ConflictError:  duplicate org_id or head user_id
#         ServiceError:   Supabase API error or unexpected failure
#     """
#     sb = _get_client()


#     logger.info("[REGISTER] Checking org uniqueness  org_id=%s", org_id)
#     try:
#         existing = (
#             sb.table("organizations")
#             .select("id")
#             .eq("org_id", org_id)
#             .execute()
#         )
#     except APIError as e:
#         logger.error("[REGISTER] Supabase error on uniqueness check: %s", e)
#         raise ServiceError(f"Database error during uniqueness check: {e.message}")

#     if existing.data:
#         logger.warning("[REGISTER] Conflict: org_id already exists  org_id=%s", org_id)
#         raise ConflictError(f"Organization ID '{org_id}' is already registered.")

    
#     logger.info("[REGISTER] Inserting organization  org_id=%s  name=%s", org_id, org_name)
#     try:
#         org_result = (
#             sb.table("organizations")
#             .insert({"org_id": org_id, "name": org_name})
#             .execute()
#         )
#     except APIError as e:
#         logger.error("[REGISTER] Failed to insert organization: code=%s msg=%s", e.code, e.message)
#         raise ServiceError(f"Failed to create organization: {e.message}")

#     if not org_result.data:
#         logger.error("[REGISTER] Organization insert returned no data")
#         raise ServiceError("Organization insert returned no data.")

#     org_uuid = org_result.data[0]["id"]
#     logger.info("[REGISTER] Organization created  org_id=%s  uuid=%s", org_id, org_uuid)

    
#     users_to_insert = [
#         {
#             "user_id": head_id,
#             "name":    "Organization Head",
#             "role":    "head",
#             "org_id":  org_uuid,
#         }
#     ]

#     clean_investigators = []
#     for inv in investigators:
#         inv_id   = (inv.get("id")   or "").strip()
#         inv_name = (inv.get("name") or "").strip()
#         if inv_id and inv_name:
#             users_to_insert.append({
#                 "user_id": inv_id,
#                 "name":    inv_name,
#                 "role":    "investigator",
#                 "org_id":  org_uuid,
#             })
#             clean_investigators.append({"id": inv_id, "name": inv_name})

#     logger.info(
#         "[REGISTER] Inserting %d user(s)  org_id=%s  head=%s  investigators=%d",
#         len(users_to_insert), org_id, head_id, len(clean_investigators),
#     )

#     #  4. Batch insert users 
#     try:
#         users_result = sb.table("users").insert(users_to_insert).execute()
#     except APIError as e:
#         logger.error("[REGISTER] Failed to insert users: code=%s msg=%s", e.code, e.message)
#         # Attempt rollback: delete the org we just created so the DB stays clean
#         try:
#             sb.table("organizations").delete().eq("id", org_uuid).execute()
#             logger.info("[REGISTER] Rollback: deleted orphaned org  uuid=%s", org_uuid)
#         except Exception as rb_err:
#             logger.error("[REGISTER] Rollback failed: %s", rb_err)
#         raise ServiceError(f"Failed to create users: {e.message}")

#     logger.info(
#         "[REGISTER] Success  org_id=%s  users_inserted=%d",
#         org_id, len(users_result.data or []),
#     )

#     return {
#         "orgId":         org_id,
#         "orgName":       org_name,
#         "orgHeadId":     head_id,
#         "investigators": clean_investigators,
#     }


def register_organization(
    org_id: str,
    org_name: str,
    head_id: str,
    investigators: list[dict],
) -> dict:
    """
    Registration flow:

    1. Verify organization exists.
    2. Verify organization name matches.
    3. Verify head exists and belongs to that organization.
    4. Create investigator accounts.
    """

    sb = _get_client()

    # --------------------------------------------------
    # STEP 1: Verify organization exists
    # --------------------------------------------------

    try:
        org_result = (
            sb.table("organizations")
            .select("id, org_id, name")
            .eq("org_id", org_id)
            .execute()
        )
    except APIError as e:
        raise ServiceError(f"Database error during organization lookup: {e.message}")

    if not org_result.data:
        raise ConflictError("Invalid Organization ID.")

    org = org_result.data[0]
    org_uuid = org["id"]

    # --------------------------------------------------
    # STEP 2: Verify organization name matches
    # --------------------------------------------------

    db_org_name = (org.get("name") or "").strip()

    if db_org_name.lower() != org_name.strip().lower():
        raise ConflictError(
            "Organization Name does not match the Organization ID."
        )

    # --------------------------------------------------
    # STEP 3: Verify head exists
    # --------------------------------------------------

    try:
        head_result = (
            sb.table("users")
            .select("id, user_id, role, org_id")
            .eq("user_id", head_id)
            .eq("role", "head")
            .eq("org_id", org_uuid)
            .execute()
        )
    except APIError as e:
        raise ServiceError(f"Database error during head lookup: {e.message}")

    if not head_result.data:
        raise ConflictError(
            "Invalid Head ID for this organization."
        )

    # --------------------------------------------------
    # STEP 4: Build investigator records
    # --------------------------------------------------

    print("INVESTIGATORS RECEIVED:")
    print(investigators)

    users_to_insert = []
    clean_investigators = []

    for inv in investigators:
        inv_id = (inv.get("id") or "").strip()
        inv_name = (inv.get("name") or "").strip()

        if not inv_id or not inv_name:
            continue

        users_to_insert.append({
            "user_id": inv_id,
            "name": inv_name,
            "role": "investigator",
            "status": "Active",
            "org_id": org_uuid,
        })

        clean_investigators.append({
            "id": inv_id,
            "name": inv_name,
        })

    # --------------------------------------------------
    # STEP 5: Insert investigators
    # --------------------------------------------------
    
    print("USERS TO INSERT:")
    print(users_to_insert)

    if users_to_insert:
        try:
            sb.table("users").insert(users_to_insert).execute()
        except APIError as e:
            print("INVESTIGATOR INSERT ERROR:", e)
            raise

    logger.info(
        "[REGISTER] Success org_id=%s investigators=%d",
        org_id,
        len(clean_investigators),
    )

    return {
        "orgId": org_id,
        "orgName": org_name,
        "orgHeadId": head_id,
        "investigators": clean_investigators,
    }



#  Login 

def login_user(org_id: str, user_id: str, role: str) -> dict:
    """
    Validate login credentials against Supabase and return the user profile.

    Steps:
        1. Resolve organizations.org_id  -> get org UUID + name
        2. Resolve users.user_id + role within that org UUID
        3. Check users.status == 'Active'

    Args:
        org_id:  e.g. "ORG-4410"
        user_id: e.g. "INV-2291" or "HEAD-0001"
        role:    "investigator" | "head"

    Returns:
        dict: { role, name, investigatorId, orgId, orgName }

    Raises:
        NotFoundError:  org not found or credentials mismatch
        ForbiddenError: account is Inactive
        ServiceError:   Supabase API error
    """
    sb = _get_client()

    #  1. Resolve organization 
    logger.info("[LOGIN] Resolving org  org_id=%s", org_id)
    try:
        org_result = (
            sb.table("organizations")
            .select("id, org_id, name")
            .eq("org_id", org_id)
            .eq("is_active", True)
            .execute()
        )
    except APIError as e:
        logger.error("[LOGIN] Supabase error on org lookup: code=%s msg=%s", e.code, e.message)
        raise ServiceError(f"Database error during org lookup: {e.message}")

    if not org_result.data:
        logger.warning("[LOGIN] Org not found  org_id=%s", org_id)
        raise NotFoundError("Invalid credentials. Check your Org ID, User ID, and role.")

    org      = org_result.data[0]
    org_uuid = org["id"]
    logger.debug("[LOGIN] Org resolved  org_id=%s  uuid=%s", org_id, org_uuid)

    #  2. Resolve user 
    logger.info("[LOGIN] Resolving user  user_id=%s  role=%s  org_uuid=%s", user_id, role, org_uuid)
    try:
        user_result = (
            sb.table("users")
            .select("user_id, name, role, status")
            .eq("org_id",  org_uuid)
            .eq("user_id", user_id)
            .eq("role",    role)
            .execute()
        )
    except APIError as e:
        logger.error("[LOGIN] Supabase error on user lookup: code=%s msg=%s", e.code, e.message)
        raise ServiceError(f"Database error during user lookup: {e.message}")

    if not user_result.data:
        logger.warning(
            "[LOGIN] User not found  user_id=%s  role=%s  org_id=%s",
            user_id, role, org_id,
        )
        raise NotFoundError("Invalid credentials. Check your Org ID, User ID, and role.")

    user = user_result.data[0]

    #  3. Status check 
    if user["status"] == "Inactive":
        logger.warning("[LOGIN] Account inactive  user_id=%s", user_id)
        raise ForbiddenError(
            "This account is inactive. Contact your Organization Head."
        )

    logger.info(
        "[LOGIN] Success  org_id=%s  user_id=%s  role=%s  name=%s",
        org_id, user_id, role, user["name"],
    )

    return {
        "role":           user["role"],
        "name":           user["name"],
        "investigatorId": user["user_id"],
        "orgId":          org["org_id"],
        "orgName":        org["name"],
    }


#  Custom exceptions 

class ConflictError(Exception):
    """Raised when a unique constraint would be violated (e.g. duplicate org_id)."""

class NotFoundError(Exception):
    """Raised when a required record does not exist."""

class ForbiddenError(Exception):
    """Raised when the account exists but is not allowed to proceed."""

class ServiceError(Exception):
    """Raised on Supabase API errors or unexpected database failures."""
