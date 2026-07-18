"""
routes/settings.py — Organization settings Blueprint.

Endpoints:
    GET    /api/v1/settings                       — Org profile + investigators.
    PUT    /api/v1/settings                       — Update org name.
    POST   /api/v1/settings/investigators         — Add an investigator.
    DELETE /api/v1/settings/investigators/<id>    — Remove an investigator.

All write operations are accessible only to the Organization Head role.
Role enforcement is currently a TODO — it will be added in the auth phase
via a decorator on each route.

Data shapes match SystemSettings.jsx form fields exactly.
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from utils.validators import require_json_fields, validate_id_format

settings_bp = Blueprint("settings", __name__)

# ── In-memory stub state (mirrors mockData.js mockInvestigator) ──────────── #
# TODO (database phase): delete these and replace every reference with
#     OrgService.get(org_id), InvestigatorService.list(org_id), etc.
_org: dict = {
    "orgName": "Sentinel Cyber Forensics",
    "orgId":   "ORG-4410",
}

_investigators: list[dict] = [
    {"name": "Aditi Rao",   "id": "INV-2291"},
    {"name": "Rohan Mehta", "id": "INV-2287"},
]


# ── GET /api/v1/settings ────────────────────────────────────────────────── #

@settings_bp.get("/settings")
def get_settings():
    """
    Return the organization profile and full investigator list.

    TODO (auth phase):
        Add role guard:  @require_role("head")

    TODO (database phase):
        Replace stub data with:
            org_id  = get_current_user_org()
            org     = OrgService.get(org_id)
            members = InvestigatorService.list(org_id=org_id)
            return success_response(data={
                "org":           org.to_dict(),
                "investigators": [m.to_dict() for m in members],
            })

    Response (200):
        {
            "data": {
                "org":           { "orgName": "...", "orgId": "..." },
                "investigators": [ { "name": "...", "id": "..." } ]
            }
        }
    """
    current_app.logger.debug("GET /settings  orgId=%s", _org["orgId"])
    return success_response(
        data={
            "org":           _org,
            "investigators": _investigators,
        }
    )


# ── PUT /api/v1/settings ─────────────────────────────────────────────────── #

@settings_bp.put("/settings")
def update_settings():
    """
    Update the organization name.

    Request body (JSON):
        { "orgName": "New Organization Name" }

    TODO (auth phase):
        Add role guard:  @require_role("head")

    TODO (database phase):
        Replace stub mutation with:
            org = OrgService.update(org_id=get_current_user_org(), name=org_name)
            return success_response(data={"org": org.to_dict()}, message="Settings updated.")

    Response (200):
        { "data": { "org": { "orgName": "...", "orgId": "..." } } }
    """
    valid, errors = require_json_fields(request, ["orgName"])
    if not valid:
        return error_response(
            message="Missing required fields.",
            status_code=400,
            error="Bad Request",
            errors=errors,
        )

    org_name = (request.get_json(silent=True) or {}).get("orgName", "").strip()

    # TODO (database phase): replace with OrgService.update(...)
    _org["orgName"] = org_name
    current_app.logger.info("Settings updated  orgName=%s", org_name)

    return success_response(data={"org": _org}, message="Settings updated.")


# ── POST /api/v1/settings/investigators ─────────────────────────────────── #

@settings_bp.post("/settings/investigators")
def add_investigator():
    """
    Add a new investigator to the organization.

    Request body (JSON):
        { "name": "Jane Doe", "id": "INV-9999" }

    TODO (auth phase):
        Add role guard:  @require_role("head")

    TODO (database phase):
        Replace stub mutation with:
            if InvestigatorService.exists(inv_id):
                return error_response("ID already exists.", 409, error="Conflict")
            inv = InvestigatorService.create(name=name, inv_id=inv_id, org_id=...)
            return success_response(data={"investigators": [...]}, status_code=201)

    Response (201):
        { "data": { "investigators": [ { "name": "...", "id": "..." } ] } }
    """
    valid, errors = require_json_fields(request, ["name", "id"])
    if not valid:
        return error_response(
            message="Missing required fields.",
            status_code=400,
            error="Bad Request",
            errors=errors,
        )

    body   = request.get_json(silent=True) or {}
    name   = body["name"].strip()
    inv_id = body["id"].strip()

    # ID format check
    id_valid, id_err = validate_id_format(inv_id, "INV")
    if not id_valid:
        return error_response(
            message=f"Invalid investigator ID: {id_err}",
            status_code=400,
            error="Bad Request",
            errors=[{"field": "id", "message": id_err}],
        )

    # Duplicate check
    # TODO (database phase): replace with InvestigatorService.exists(inv_id)
    if any(i["id"] == inv_id for i in _investigators):
        return error_response(
            message=f"Investigator ID '{inv_id}' already exists.",
            status_code=409,
            error="Conflict",
        )

    # TODO (database phase): replace with InvestigatorService.create(...)
    _investigators.append({"name": name, "id": inv_id})
    current_app.logger.info("Investigator added  name=%s  id=%s", name, inv_id)

    return success_response(
        data={"investigators": _investigators},
        message="Investigator added.",
        status_code=201,
    )


# ── DELETE /api/v1/settings/investigators/<inv_id> ──────────────────────── #

@settings_bp.delete("/settings/investigators/<string:inv_id>")
def remove_investigator(inv_id: str):
    """
    Remove an investigator from the organization.

    TODO (auth phase):
        Add role guard:  @require_role("head")

    TODO (database phase):
        Replace stub mutation with:
            deleted = InvestigatorService.delete(inv_id, org_id=get_current_user_org())
            if not deleted:
                return error_response(f"Investigator '{inv_id}' not found.", 404)
            return success_response(data={"investigators": [...]}, message="Investigator removed.")

    Response (200): updated investigators list
    Response (404): if inv_id not found
    """
    global _investigators

    before = len(_investigators)
    # TODO (database phase): replace with InvestigatorService.delete(inv_id)
    _investigators = [i for i in _investigators if i["id"] != inv_id]

    if len(_investigators) == before:
        return error_response(
            message=f"Investigator '{inv_id}' not found.",
            status_code=404,
            error="Not Found",
        )

    current_app.logger.info("Investigator removed  id=%s", inv_id)
    return success_response(
        data={"investigators": _investigators},
        message="Investigator removed.",
    )
