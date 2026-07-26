"""
routes/auth.py — Authentication Blueprint (stub).

Endpoints:
    POST /api/v1/auth/login     — Authenticate a user by org + user ID + role.
    POST /api/v1/auth/register  — Register a new organization.

Both endpoints perform real input validation and return the exact JSON
shape the React frontend expects. Credential checking against a database
is stubbed — see TODO markers for exact integration points.

Request / Response contracts are documented on each view function.
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from utils.validators import require_json_fields, validate_id_format

auth_bp = Blueprint("auth", __name__)


# ── POST /api/v1/auth/login ─────────────────────────────────────────────── #

@auth_bp.post("/auth/login")
def login():
    """
    Authenticate a user (stub — no DB lookup yet).

    Request body (JSON):
        {
            "orgId":  "ORG-XXXX",   required
            "userId": "INV-XXXX",   required  (INV- or HEAD- prefix)
            "role":   "investigator" | "head"  required
        }

    Response (200):
        {
            "status":  "success",
            "message": "Login successful.",
            "data": {
                "role":           "investigator",
                "name":           "Aditi Rao",
                "investigatorId": "INV-2291",
                "orgId":          "ORG-4410",
                "orgName":        "Sentinel Cyber Forensics"
            }
        }

    TODO (auth phase):
        Replace the stub return below with:
            user = UserService.authenticate(org_id, user_id, role)
            if not user:
                return error_response("Invalid credentials.", 401, error="Unauthorized")
            token = TokenService.generate(user)
            return success_response(data={**user.to_dict(), "token": token})
    """
    body = request.get_json(silent=True) or {}
    current_app.logger.debug("Login attempt  orgId=%s  role=%s", body.get("orgId"), body.get("role"))

    # ── Validate required fields ─────────────────────────────────────── #
    valid, errors = require_json_fields(request, ["orgId", "userId", "role"])
    if not valid:
        return error_response(
            message="Missing required fields.",
            status_code=400,
            error="Bad Request",
            errors=errors,
        )

    org_id  = body["orgId"].strip()
    user_id = body["userId"].strip()
    role    = body["role"].strip()

    if role not in ("investigator", "head"):
        return error_response(
            message="role must be 'investigator' or 'head'.",
            status_code=400,
            error="Bad Request",
            errors=[{"field": "role", "message": "Must be 'investigator' or 'head'."}],
        )

    # ── TODO (database phase): look up real user ──────────────────────── #
    # user = UserService.get_by_org_and_id(org_id=org_id, user_id=user_id, role=role)
    # if not user:
    #     return error_response("Invalid credentials.", 401, error="Unauthorized")

    # ── Stub response — mirrors mockData.js mockInvestigator shape ────── #
    return success_response(
        data={
            "role":           role,
            "name":           "Aditi Rao",                 # TODO: from DB user record
            "investigatorId": user_id,
            "orgId":          org_id,
            "orgName":        "Sentinel Cyber Forensics",  # TODO: from DB org record
        },
        message="Login successful.",
        status_code=200,
    )


# ── POST /api/v1/auth/register ──────────────────────────────────────────── #

@auth_bp.post("/auth/register")
def register():
    """
    Register a new organization (stub — no DB insert yet).

    Request body (JSON):
        {
            "orgName":       "Sentinel Cyber Forensics",  required
            "orgId":         "ORG-4410",                  required
            "orgHeadId":     "HEAD-0001",                 required
            "investigators": [                            optional
                { "name": "Aditi Rao", "id": "INV-2291" }
            ]
        }

    Response (201):
        {
            "status":  "success",
            "message": "Organization registered successfully.",
            "data": {
                "orgId":         "ORG-4410",
                "orgName":       "Sentinel Cyber Forensics",
                "orgHeadId":     "HEAD-0001",
                "investigators": [ ... ]
            }
        }

    TODO (database phase):
        Replace the stub return below with:
            if OrgService.exists(org_id):
                return error_response("Org ID already taken.", 409, error="Conflict")
            org = OrgService.create(org_name, org_id, org_head_id, investigators)
            return success_response(data=org.to_dict(), status_code=201)
    """
    body = request.get_json(silent=True) or {}
    current_app.logger.debug("Register attempt  orgId=%s", body.get("orgId"))

    # ── Validate required fields ─────────────────────────────────────── #
    valid, errors = require_json_fields(request, ["orgName", "orgId", "orgHeadId"])
    if not valid:
        return error_response(
            message="Missing required fields.",
            status_code=400,
            error="Bad Request",
            errors=errors,
        )

    org_id     = body["orgId"].strip()
    org_name   = body["orgName"].strip()
    org_head   = body["orgHeadId"].strip()
    investigators = body.get("investigators", [])

    # ── ID format validation ─────────────────────────────────────────── #
    org_valid, org_err = validate_id_format(org_id, "ORG")
    if not org_valid:
        return error_response(
            message=f"Invalid orgId: {org_err}",
            status_code=400,
            error="Bad Request",
            errors=[{"field": "orgId", "message": org_err}],
        )

    head_valid, head_err = validate_id_format(org_head, "HEAD")
    if not head_valid:
        return error_response(
            message=f"Invalid orgHeadId: {head_err}",
            status_code=400,
            error="Bad Request",
            errors=[{"field": "orgHeadId", "message": head_err}],
        )

    # ── TODO (database phase): check uniqueness and persist ──────────── #
    # if OrgService.exists(org_id):
    #     return error_response("Org ID already registered.", 409, error="Conflict")
    # org = OrgService.create(
    #     name=org_name, org_id=org_id,
    #     head_id=org_head, investigators=investigators
    # )

    current_app.logger.info("Register (stub)  orgId=%s  orgName=%s", org_id, org_name)

    return success_response(
        data={
            "orgId":         org_id,
            "orgName":       org_name,
            "orgHeadId":     org_head,
            "investigators": investigators,
        },
        message="Organization registered successfully.",
        status_code=201,
    )
