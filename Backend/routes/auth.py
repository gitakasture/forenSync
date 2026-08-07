"""
routes/auth.py -- Authentication Blueprint.

Endpoints:
    POST /api/v1/auth/register  -- Register a new organization + users.
    POST /api/v1/auth/login     -- Authenticate a user against Supabase.

Thin handler: validates input, delegates all DB work to services/auth_service.py,
formats responses with utils/response.py. No Supabase client code lives here.

Frontend contract (must not change):
    Register request:  { orgName, orgId, orgHeadId, investigators? }
    Register response: 201 { orgId, orgName, orgHeadId, investigators }
    Login request:     { orgId, userId, role }
    Login response:    200 { role, name, investigatorId, orgId, orgName }
"""

from flask import Blueprint, request, current_app

from utils.response import success_response, error_response
from utils.validators import require_json_fields
from services.auth_service import (
    register_organization,
    login_user,
    ConflictError,
    NotFoundError,
    ForbiddenError,
    ServiceError,
)

auth_bp = Blueprint("auth", __name__)


# POST /api/v1/auth/register
@auth_bp.post("/auth/register")
def register():
    """
    Register a new organization with its head user and optional investigators.

    Request body (JSON):
        {
            "orgName":        "Sentinel Cyber Forensics",  required
            "orgId":          "ORG-4410",                  required
            "orgHeadId":      "HEAD-0001",                 required
            "investigators":  [{ "name": "...", "id": "..." }]  optional
        }

    Response 201:
        { "status": "success", "data": { orgId, orgName, orgHeadId, investigators } }
    """
    body = request.get_json(silent=True) or {}
    print("REGISTER REQUEST:")
    print(body)
    current_app.logger.debug("Register attempt  orgId=%s", body.get("orgId"))

    valid, errors = require_json_fields(request, ["orgName", "orgId", "orgHeadId"])
    if not valid:
        return error_response("Missing required fields.", 400, "Bad Request", errors)

    org_id        = body["orgId"].strip()
    org_name      = body["orgName"].strip()
    head_id       = body["orgHeadId"].strip()
    investigators = body.get("investigators", [])

    # org_valid, org_err = validate_id_format(org_id, "ORG")
    # if not org_valid:
    #     return error_response(
    #         f"Invalid orgId: {org_err}", 400, "Bad Request",
    #         [{"field": "orgId", "message": org_err}],
    #     )

    # head_valid, head_err = validate_id_format(head_id, "HEAD")
    # if not head_valid:
    #     return error_response(
    #         f"Invalid orgHeadId: {head_err}", 400, "Bad Request",
    #         [{"field": "orgHeadId", "message": head_err}],
    #     )

    try:
        result = register_organization(org_id, org_name, head_id, investigators)
        return success_response(
            data=result,
            message="Organization registered successfully.",
            status_code=201,
        )
    except ConflictError as e:
        current_app.logger.warning("Register conflict  orgId=%s  %s", org_id, e)
        return error_response(str(e), 409, "Conflict")
    except (EnvironmentError, ServiceError) as e:
        current_app.logger.error("Register service error: %s", e)
        return error_response("Registration failed. Please try again.", 500, "Internal Server Error")
    # except Exception as e:
    #     current_app.logger.error("Register unexpected error: %s", e)
    #     return error_response("An unexpected error occurred.", 500, "Internal Server Error")
    except Exception as e:
        current_app.logger.exception(e)
        return error_response(
            str(e),
            500,
            "Internal Server Error"
        )


# POST /api/v1/auth/login
@auth_bp.post("/auth/login")
def login():
    """
    Authenticate a user by org ID, user ID, and role.

    Request body (JSON):
        { "orgId": "ORG-4410", "userId": "INV-2291", "role": "investigator" }

    Response 200:
        { "status": "success", "data": { role, name, investigatorId, orgId, orgName } }
    """
    body = request.get_json(silent=True) or {}
    current_app.logger.debug(
        "Login attempt  orgId=%s  role=%s", body.get("orgId"), body.get("role")
    )

    valid, errors = require_json_fields(request, ["orgId", "userId", "role"])
    if not valid:
        return error_response("Missing required fields.", 400, "Bad Request", errors)

    org_id  = body["orgId"].strip()
    user_id = body["userId"].strip()
    role    = body["role"].strip()

    if role not in ("investigator", "head"):
        return error_response(
            "role must be 'investigator' or 'head'.", 400, "Bad Request",
            [{"field": "role", "message": "Must be 'investigator' or 'head'."}],
        )

    try:
        result = login_user(org_id, user_id, role)
        return success_response(data=result, message="Login successful.", status_code=200)
    except NotFoundError as e:
        current_app.logger.warning(
            "Login failed  orgId=%s  userId=%s  reason=%s", org_id, user_id, e
        )
        return error_response(str(e), 401, "Unauthorized")
    except ForbiddenError as e:
        current_app.logger.warning(
            "Login blocked  orgId=%s  userId=%s  reason=%s", org_id, user_id, e
        )
        return error_response(str(e), 403, "Forbidden")
    except (EnvironmentError, ServiceError) as e:
        current_app.logger.error("Login service error: %s", e)
        return error_response("Login failed. Please try again.", 500, "Internal Server Error")
    except Exception as e:
        current_app.logger.error("Login unexpected error: %s", e)
        return error_response("An unexpected error occurred.", 500, "Internal Server Error")
