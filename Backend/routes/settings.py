"""
routes/settings.py — Organization settings Blueprint with Database Integration.

Endpoints:
    GET    /api/v1/settings                       — Org profile + investigators.
    PUT    /api/v1/settings                       — Update org name.
    POST   /api/v1/settings/investigators         — Add an investigator.
    DELETE /api/v1/settings/investigators/<id>    — Remove an investigator.
"""

from flask import Blueprint, request, current_app
from models import db, Organization, User
from utils.response import success_response, error_response
from utils.validators import require_json_fields, validate_id_format

settings_bp = Blueprint("settings", __name__)


@settings_bp.get("/settings")
def get_settings():
    """
    Return the organization profile and full investigator list from Database.
    """
    org = Organization.query.filter_by(org_id="ORG-4410").first()
    if not org:
        org = Organization(org_id="ORG-4410", name="Sentinel Cyber Forensics", org_head_id="HEAD-0001")
        db.session.add(org)
        db.session.commit()

    investigators = User.query.filter_by(org_id=org.org_id, role="investigator").all()
    inv_list = [{"name": i.name, "id": i.user_id} for i in investigators]

    return success_response(
        data={
            "org": {"orgName": org.name, "orgId": org.org_id},
            "investigators": inv_list,
        }
    )


@settings_bp.put("/settings")
def update_settings():
    """
    Update the organization name in Database.
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

    org = Organization.query.filter_by(org_id="ORG-4410").first()
    if not org:
        org = Organization(org_id="ORG-4410", name=org_name, org_head_id="HEAD-0001")
        db.session.add(org)
    else:
        org.name = org_name

    db.session.commit()

    return success_response(
        data={"org": {"orgName": org.name, "orgId": org.org_id}},
        message="Settings updated.",
    )


@settings_bp.post("/settings/investigators")
def add_investigator():
    """
    Add a new investigator to the organization in Database.
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

    id_valid, id_err = validate_id_format(inv_id, "INV")
    if not id_valid:
        return error_response(
            message=f"Invalid investigator ID: {id_err}",
            status_code=400,
            error="Bad Request",
            errors=[{"field": "id", "message": id_err}],
        )

    existing = User.query.filter_by(user_id=inv_id).first()
    if existing:
        return error_response(
            message=f"Investigator ID '{inv_id}' already exists.",
            status_code=409,
            error="Conflict",
        )

    new_inv = User(user_id=inv_id, name=name, role="investigator", org_id="ORG-4410")
    db.session.add(new_inv)
    db.session.commit()

    investigators = User.query.filter_by(org_id="ORG-4410", role="investigator").all()
    inv_list = [{"name": i.name, "id": i.user_id} for i in investigators]

    return success_response(
        data={"investigators": inv_list},
        message="Investigator added.",
        status_code=201,
    )


@settings_bp.delete("/settings/investigators/<string:inv_id>")
def remove_investigator(inv_id: str):
    """
    Remove an investigator from the organization in Database.
    """
    user = User.query.filter_by(user_id=inv_id, org_id="ORG-4410").first()
    if not user:
        return error_response(
            message=f"Investigator '{inv_id}' not found.",
            status_code=404,
            error="Not Found",
        )

    db.session.delete(user)
    db.session.commit()

    investigators = User.query.filter_by(org_id="ORG-4410", role="investigator").all()
    inv_list = [{"name": i.name, "id": i.user_id} for i in investigators]

    return success_response(
        data={"investigators": inv_list},
        message="Investigator removed.",
    )
