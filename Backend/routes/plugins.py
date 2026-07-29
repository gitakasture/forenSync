"""
routes/plugins.py — Plugins Blueprint with Database Integration.

Endpoints:
    GET  /api/v1/plugins          — List active plugin + all supported formats from Database.
    POST /api/v1/plugins/activate — Set active parser plugin in Database.
"""

from flask import Blueprint, request, current_app
from models import db, Plugin
from utils.response import success_response, error_response
from utils.validators import require_json_fields

plugins_bp = Blueprint("plugins", __name__)

_SUPPORTED_FORMATS: list[dict] = [
    {"id": "linux-auth",    "label": "Linux Auth Log Parser"},
    {"id": "apache-access", "label": "Apache Access Log Parser"},
    {"id": "custom",        "label": "Develop Custom Plugin"},
]


@plugins_bp.get("/plugins")
def list_plugins():
    """
    Return active plugin and all supported plugin formats from Database.
    """
    active = Plugin.query.filter_by(org_id="ORG-4410", is_active=True).first()
    current_plugin = active.to_dict() if active else None

    return success_response(
        data={
            "currentPlugin": current_plugin,
            "supportedFormats": _SUPPORTED_FORMATS,
        }
    )


@plugins_bp.post("/plugins/activate")
def activate_plugin():
    """
    Set active parser plugin for the organization in Database.
    """
    valid, errors = require_json_fields(request, ["pluginId"])
    if not valid:
        return error_response(
            message="Missing required fields.",
            status_code=400,
            error="Bad Request",
            errors=errors,
        )

    plugin_id = (request.get_json(silent=True) or {}).get("pluginId", "").strip()

    fmt = next((f for f in _SUPPORTED_FORMATS if f["id"] == plugin_id), None)
    if not fmt:
        return error_response(
            message=f"Unknown plugin ID: '{plugin_id}'. Valid IDs: {[f['id'] for f in _SUPPORTED_FORMATS]}",
            status_code=404,
            error="Not Found",
        )

    # Deactivate any existing active plugin
    Plugin.query.filter_by(org_id="ORG-4410").update({"is_active": False})

    # Activate requested plugin
    plugin = Plugin.query.filter_by(org_id="ORG-4410", plugin_id=plugin_id).first()
    if not plugin:
        plugin = Plugin(plugin_id=plugin_id, label=fmt["label"], is_active=True, org_id="ORG-4410", added_on="today")
        db.session.add(plugin)
    else:
        plugin.is_active = True

    db.session.commit()

    return success_response(
        data={"currentPlugin": plugin.to_dict()},
        message="Plugin activated.",
    )
