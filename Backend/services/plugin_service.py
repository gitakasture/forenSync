"""
services/plugin_service.py — Plugin marketplace + format detection.
"""

import logging
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError
from plugins.registry import PLUGIN_CATALOG, list_available_plugins, detect_format

logger = logging.getLogger(__name__)


def _resolve_org_uuid(sb, org_id: str) -> str:
    result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
    if not result.data:
        raise NotFoundError(f"Organization '{org_id}' not found.")
    return result.data[0]["id"]


def list_plugins_for_org(org_id: str) -> list[dict]:
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)
        added_result = sb.table("org_plugins").select("plugin_name, added_at").eq("org_id", org_uuid).execute()
        added_map = {row["plugin_name"]: row["added_at"] for row in (added_result.data or [])}

        plugins = []
        for name in list_available_plugins():
            catalog_entry = PLUGIN_CATALOG.get(name, {"label": name, "description": ""})
            plugins.append({
                "name": name,
                "label": catalog_entry["label"],
                "description": catalog_entry["description"],
                "added": name in added_map,
            })
        return plugins
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def add_plugin_to_org(org_id: str, plugin_name: str) -> dict:
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)
        if plugin_name not in list_available_plugins():
            raise NotFoundError(f"Plugin '{plugin_name}' does not exist.")

        existing = sb.table("org_plugins").select("id").eq("org_id", org_uuid).eq("plugin_name", plugin_name).execute()
        if existing.data:
            return {"added": True}

        sb.table("org_plugins").insert({"org_id": org_uuid, "plugin_name": plugin_name}).execute()
        logger.info("[PLUGINS] Added  org_id=%s  plugin=%s", org_id, plugin_name)
        return {"added": True}
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def remove_plugin_from_org(org_id: str, plugin_name: str) -> dict:
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)
        sb.table("org_plugins").delete().eq("org_id", org_uuid).eq("plugin_name", plugin_name).execute()
        logger.info("[PLUGINS] Removed  org_id=%s  plugin=%s", org_id, plugin_name)
        return {"removed": True}
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def match_parsers_for_case(org_id: str, case_id: str) -> list[dict]:
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)

        added_result = sb.table("org_plugins").select("plugin_name").eq("org_id", org_uuid).execute()
        added_names = {row["plugin_name"] for row in (added_result.data or [])}
        if not added_names:
            raise ServiceError("No plugins have been added to this organization. Add plugins from the Parser Plugins page first.")

        case_result = sb.table("cases").select("id").eq("org_id", org_uuid).eq("case_id", case_id).execute()
        if not case_result.data:
            raise NotFoundError(f"Case '{case_id}' not found.")
        case_uuid = case_result.data[0]["id"]

        files_result = (
            sb.table("case_files").select("id, file_name, storage_path")
            .eq("case_id", case_uuid).eq("file_category", "log").execute()
        )

        results = []
        for f in (files_result.data or []):
            file_bytes = sb.storage.from_("case-files").download(f["storage_path"])
            all_scores = detect_format(file_bytes)
            filtered = [(name, score) for name, score in all_scores if name in added_names]

            best_name, best_confidence = (filtered[0] if filtered else (None, 0.0))

            results.append({
                "fileId": f["id"],
                "fileName": f["file_name"],
                "matchedPlugin": best_name,
                "confidence": round(best_confidence * 100),
                "alternatives": [n for n, _ in filtered if n != best_name],
            })
        return results
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")