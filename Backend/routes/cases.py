"""
routes/cases.py — Cases Blueprint.

Endpoints:
    GET  /api/v1/cases            — List all cases for the org.
    POST /api/v1/cases            — Create a new case.
    GET  /api/v1/cases/<case_id>  — Get a single case by ID.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, current_app
from models import db, Case
from utils.response import success_response, error_response

cases_bp = Blueprint("cases", __name__)


@cases_bp.get("/cases")
def list_cases():
    """
    Return all cases stored in the database.
    """
    cases = Case.query.order_by(Case.id.desc()).all()
    case_list = [c.to_dict() for c in cases]
    current_app.logger.debug("GET /cases — returning %d database cases", len(case_list))
    return success_response(
        data={"cases": case_list, "total": len(case_list)},
    )


@cases_bp.post("/cases")
def create_case():
    """
    Create a new case in the database.
    """
    content_type = request.content_type or ""
    is_multipart = "multipart/form-data" in content_type

    if is_multipart:
        name        = (request.form.get("name")        or "").strip()
        description = (request.form.get("description") or "").strip()
        date_from   = (request.form.get("from")        or "").strip()
        date_to     = (request.form.get("to")          or "").strip()
    else:
        body        = request.get_json(silent=True) or {}
        name        = (body.get("name")        or "").strip()
        description = (body.get("description") or "").strip()
        date_from   = (body.get("from")        or "").strip()
        date_to     = (body.get("to")          or "").strip()

    if not name:
        return error_response(
            message="Case name is required.",
            status_code=400,
            error="Bad Request",
            errors=[{"field": "name", "message": "This field is required."}],
        )

    # Generate sequential or unique CASE-ID
    last_case = Case.query.order_by(Case.id.desc()).first()
    new_num = (last_case.id + 1000 + 1) if last_case else 1043
    case_id = f"CASE-{new_num}"

    timeframe = "—"
    if date_from or date_to:
        timeframe = f"{date_from or '?'} – {date_to or '?'}"

    last_modified = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    new_case = Case(
        case_id=case_id,
        name=name,
        description=description,
        date_from=date_from,
        date_to=date_to,
        timeframe=timeframe,
        last_modified=last_modified,
        status="Active",
        action="Open",
        org_id="ORG-4410",
    )

    db.session.add(new_case)
    db.session.commit()

    current_app.logger.info("POST /cases — created case %s (%s)", case_id, name)

    return success_response(
        data=new_case.to_dict(),
        message="Case created successfully.",
        status_code=201,
    )


@cases_bp.get("/cases/<string:case_id>")
def get_case(case_id: str):
    """
    Return a single case by case_id.
    """
    case = Case.query.filter_by(case_id=case_id).first()
    if not case:
        return error_response(
            message=f"Case '{case_id}' not found.",
            status_code=404,
            error="Not Found",
        )

    current_app.logger.debug("GET /cases/%s — found in database", case_id)
    return success_response(data={"case": case.to_dict()})
