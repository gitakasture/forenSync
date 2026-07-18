"""
routes/plugins.py — Plugins Blueprint.

Endpoints:
    GET  /api/v1/plugins          — List active plugin + all supported formats.
    POST /api/v1/plugins/activate — Set the active parser plugin.

Response shapes match mockData.js exactly:
    currentPlugin:    null | { "name": "...", "addedOn": "..." }
    supportedFormats: [ { "id": "...", "label": "..." } ]
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from utils.validators import require_json_fields

plugins_bp = Blueprint("plugins", __name__)

# ── Supported formats (mirrors mockData.js supportedFormats) ─────────────── #
# TODO (database phase): load these from a Plugin table instead
_SUPPORTED_FORMATS: list[dict] = [
    {"id": "linux-auth",    "label": "Linux Auth Log Parser"},
    {"id": "apache-access", "label": "Apache Access Log Parser"},
    {"id": "custom",        "label": "Develop Custom Plugin"},
]

# In-memory active plugin — will be persisted to DB later
# TODO (database phase): replace with PluginService.get_active()
_active_plugin: dict | None = None


# ── GET /api/v1/plugins ─────────────────────────────────────────────────── #

@plugins_bp.get("/plugins")
def list_plugins():
    """
    Return the currently active plugin and all available formats.

    TODO (database phase):
        Replace stub data with:
            active   = PluginService.get_active(org_id=get_current_user_org())
            formats  = PluginService.list_supported()
            return success_response(data={
                "currentPlugin":    active.to_dict() if active else None,
                "supportedFormats": [f.to_dict() for f in formats],
            })

    TODO (parser phase):
        Each format entry should include a "status" field indicating
        whether the parser module is loaded and healthy:
            { "id": "linux-auth", "label": "...", "status": "ready" | "error" }

    Response (200):
        {
            "status": "success",
            "data": {
                "currentPlugin":    null | { "name": "...", "addedOn": "..." },
                "supportedFormats": [ { "id": "...", "label": "..." } ]
            }
        }
    """
    current_app.logger.debug("GET /plugins  active=%s", _active_plugin)
    return success_response(
        data={
            "currentPlugin":    _active_plugin,
            "supportedFormats": _SUPPORTED_FORMATS,
        }
    )


# ── POST /api/v1/plugins/activate ───────────────────────────────────────── #

@plugins_bp.post("/plugins/activate")
def activate_plugin():
    """
    Set the active parser plugin for the organization.

    Request body (JSON):
        { "pluginId": "linux-auth" | "apache-access" | "custom" }

    TODO (database phase):
        Replace in-memory state mutation with:
            plugin = PluginService.get(plugin_id)
            if not plugin:
                return error_response(..., 404)
            PluginService.set_active(org_id=get_current_user_org(), plugin_id=plugin_id)
            return success_response(data={"currentPlugin": plugin.to_dict()})

    TODO (parser phase):
        After activation, validate the plugin module can be loaded:
            ok, err = PluginRegistry.validate(plugin_id)
            if not ok:
                return error_response(f"Plugin failed health check: {err}", 500)

    Response (200):
        {
            "status":  "success",
            "message": "Plugin activated.",
            "data":    { "currentPlugin": { "name": "...", "addedOn": "..." } }
        }
    """
    global _active_plugin

    valid, errors = require_json_fields(request, ["pluginId"])
    if not valid:
        return error_response(
            message="Missing required fields.",
            status_code=400,
            error="Bad Request",
            errors=errors,
        )

    plugin_id = (request.get_json(silent=True) or {}).get("pluginId", "").strip()

    # TODO (database phase): replace with PluginService.get(plugin_id)
    fmt = next((f for f in _SUPPORTED_FORMATS if f["id"] == plugin_id), None)
    if not fmt:
        return error_response(
            message=f"Unknown plugin ID: '{plugin_id}'. "
                    f"Valid IDs: {[f['id'] for f in _SUPPORTED_FORMATS]}",
            status_code=404,
            error="Not Found",
        )

    _active_plugin = {"name": fmt["label"], "addedOn": "today"}
    current_app.logger.info("Plugin activated: %s", plugin_id)

    return success_response(
        data={"currentPlugin": _active_plugin},
        message="Plugin activated.",
    )
