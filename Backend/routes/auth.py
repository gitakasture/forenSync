"""
routes/auth.py — Authentication Blueprint (Supabase backend).

Endpoints:
    POST /api/v1/auth/register  — Register a new organization + users in Supabase.
    POST /api/v1/auth/login     — Authenticate a user against Supabase.
"""

import os
from flask import Blueprint, request, current_app
from supabase import create_client, Client
from utils.response import success_response, error_response
from utils.validators import require_json_fields, validate_id_format

auth_bp = Blueprint("auth", __name__)


def get_supabase() -> Client:
    """Return a Supabase client using env credentials."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    return create_client(url, key)


# ──────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/register
# Body: { orgName, orgId, orgHeadId, investigators: [{name, id}, ...] }
# ──────────────────────────────────────────────────────────────────────────
@auth_bp.post("/auth/register")
def register():
    body = request.get_json(silent=True) or {}

    # Validate required fields
    valid, errors = require_json_fields(request, ["orgName", "orgId", "orgHeadId"])
    if not valid:
        return error_response("Missing required fields.", 400, "Bad Request", errors)

    org_id       = body["orgId"].strip()
    org_name     = body["orgName"].strip()
    head_id      = body["orgHeadId"].strip()
    investigators = body.get("investigators", [])

    # Validate ID formats
    org_valid, org_err = validate_id_format(org_id, "ORG")
    if not org_valid:
        return error_response(f"Invalid orgId: {org_err}", 400, "Bad Request",
                              [{"field": "orgId", "message": org_err}])

    head_valid, head_err = validate_id_format(head_id, "HEAD")
    if not head_valid:
        return error_response(f"Invalid orgHeadId: {head_err}", 400, "Bad Request",
                              [{"field": "orgHeadId", "message": head_err}])

    try:
        sb = get_supabase()

        # Check org doesn't already exist
        existing = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if existing.data:
            return error_response(
                f"Organization ID '{org_id}' is already registered.",
                409, "Conflict"
            )

        # Insert organization
        org_result = sb.table("organizations").insert({
            "org_id":  org_id,
            "name":    org_name,
            "head_id": head_id,
        }).execute()

        org_uuid = org_result.data[0]["id"]

        # Insert the org head as a user
        users_to_insert = [{
            "user_id": head_id,
            "name":    "Organization Head",
            "role":    "head",
            "org_id":  org_uuid,
        }]

        # Insert investigators
        for inv in investigators:
            inv_id   = inv.get("id", "").strip()
            inv_name = inv.get("name", "").strip()
            if inv_id and inv_name:
                users_to_insert.append({
                    "user_id": inv_id,
                    "name":    inv_name,
                    "role":    "investigator",
                    "org_id":  org_uuid,
                })

        sb.table("users").insert(users_to_insert).execute()

        current_app.logger.info("Registered org=%s head=%s", org_id, head_id)

        return success_response(
            data={
                "orgId":         org_id,
                "orgName":       org_name,
                "orgHeadId":     head_id,
                "investigators": investigators,
            },
            message="Organization registered successfully.",
            status_code=201,
        )

    except EnvironmentError as e:
        current_app.logger.error("Supabase config error: %s", e)
        return error_response(str(e), 500, "Configuration Error")
    except Exception as e:
        current_app.logger.error("Register error: %s", e)
        return error_response("Registration failed. Please try again.", 500, "Internal Server Error")


# ──────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/login
# Body: { orgId, userId, role }
# ──────────────────────────────────────────────────────────────────────────
@auth_bp.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}

    valid, errors = require_json_fields(request, ["orgId", "userId", "role"])
    if not valid:
        return error_response("Missing required fields.", 400, "Bad Request", errors)

    org_id  = body["orgId"].strip()
    user_id = body["userId"].strip()
    role    = body["role"].strip()

    if role not in ("investigator", "head"):
        return error_response(
            "role must be 'investigator' or 'head'.", 400, "Bad Request",
            [{"field": "role", "message": "Must be 'investigator' or 'head'."}]
        )

    try:
        sb = get_supabase()

        # 1. Look up the organization
        org_result = sb.table("organizations") \
            .select("id, org_id, name, head_id") \
            .eq("org_id", org_id) \
            .eq("is_active", True) \
            .execute()

        if not org_result.data:
            return error_response(
                f"Organization '{org_id}' not found.", 404, "Not Found"
            )

        org      = org_result.data[0]
        org_uuid = org["id"]

        # 2. Look up the user in that org with the correct role
        user_result = sb.table("users") \
            .select("user_id, name, role, status") \
            .eq("org_id", org_uuid) \
            .eq("user_id", user_id) \
            .eq("role", role) \
            .execute()

        if not user_result.data:
            return error_response(
                "Invalid credentials. Check your Org ID, User ID, and role.",
                401, "Unauthorized"
            )

        user = user_result.data[0]

        if user["status"] == "Inactive":
            return error_response(
                "This account is inactive. Contact your Organization Head.",
                403, "Forbidden"
            )

        current_app.logger.info("Login ok  org=%s  user=%s  role=%s", org_id, user_id, role)

        return success_response(
            data={
                "role":           user["role"],
                "name":           user["name"],
                "investigatorId": user["user_id"],
                "orgId":          org["org_id"],
                "orgName":        org["name"],
            },
            message="Login successful.",
            status_code=200,
        )

    except EnvironmentError as e:
        current_app.logger.error("Supabase config error: %s", e)
        return error_response(str(e), 500, "Configuration Error")
    except Exception as e:
        current_app.logger.error("Login error: %s", e)
        return error_response("Login failed. Please try again.", 500, "Internal Server Error")
