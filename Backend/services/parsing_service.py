"""
services/parsing_service.py — Runs actual parser plugins against uploaded
case files and stores the resulting structured events.
"""

import logging
import hashlib
import tempfile
import os
from datetime import datetime
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError
from plugins.registry import get_plugin

logger = logging.getLogger(__name__)

BUCKET_NAME = "case-files"
BATCH_SIZE = 500


def _resolve_org_uuid(sb, org_id: str) -> str:
    result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
    if not result.data:
        raise NotFoundError(f"Organization '{org_id}' not found.")
    return result.data[0]["id"]


def parse_case_files(org_id: str, case_id: str, matches: list[dict]) -> dict:
    """
    matches: [{"fileId": "<case_files.id>", "pluginName": "auth_log"}, ...]
    Every uploaded log file for this case MUST be present in `matches`
    with a non-empty pluginName — enforced by the caller (route layer).
    """
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)

        case_result = sb.table("cases").select("id, incident_from").eq("org_id", org_uuid).eq("case_id", case_id).execute()
        if not case_result.data:
            raise NotFoundError(f"Case '{case_id}' not found.")
        case_row = case_result.data[0]
        case_uuid = case_row["id"]

        starting_year = None
        if case_row.get("incident_from"):
            starting_year = int(case_row["incident_from"].split("-")[0])

        # Clear any previous parse attempt for this case (re-parsing is idempotent)
        sb.table("events").delete().eq("case_id", case_uuid).execute()

        total_events = 0

        for match in matches:
            file_id = match["fileId"]
            plugin_name = match["pluginName"]

            file_result = sb.table("case_files").select("file_name, storage_path").eq("id", file_id).execute()
            if not file_result.data:
                raise ServiceError(f"File '{file_id}' not found.")
            file_row = file_result.data[0]

            file_bytes = sb.storage.from_(BUCKET_NAME).download(file_row["storage_path"])

            kwargs = {"starting_year": starting_year} if starting_year else {}
            parser = get_plugin(plugin_name, **kwargs)

            # Parsers expect a filepath, not raw bytes — write to a temp file
            suffix = ".evtx" if plugin_name == "windows_event_log" else ".log"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                events = parser.parse(tmp_path)
            finally:
                os.remove(tmp_path)

            rows = []
            for e in events:
                raw_log_hash = hashlib.sha256(e["raw_log"].encode("utf-8", errors="ignore")).hexdigest()
                rows.append({
                    "case_id": case_uuid,
                    "case_file_id": file_id,
                    "source": e["source"],
                    "host": e["host"],
                    "actor": e["actor"],
                    "action": e["action"],
                    "object": e["object"],
                    "result": e["result"],
                    "raw_log": e["raw_log"],
                    "raw_log_hash": raw_log_hash,
                    "timestamp": e["timestamp"] if e["timestamp"] != "unknown" else None,
                })

            for i in range(0, len(rows), BATCH_SIZE):
                sb.table("events").insert(rows[i:i + BATCH_SIZE]).execute()

            total_events += len(rows)
            logger.info("[PARSE] file=%s plugin=%s events=%d", file_row["file_name"], plugin_name, len(rows))

        logger.info("[PARSE] Complete  case_id=%s  total_events=%d", case_id, total_events)
        return {"caseId": case_id, "filesParsed": len(matches), "totalEvents": total_events}

    except APIError as e:
        logger.error("[PARSE] Supabase error: %s", e)
        raise ServiceError(f"Database error during parsing: {e.message}")

def get_parse_status_for_case(org_id: str, case_id: str) -> list[dict]:
    """
    For each log file in this case, check if it's already been parsed.
    Returns per-file: matched plugin (derived from events.source) and event count.
    """
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)

        case_result = sb.table("cases").select("id").eq("org_id", org_uuid).eq("case_id", case_id).execute()
        if not case_result.data:
            raise NotFoundError(f"Case '{case_id}' not found.")
        case_uuid = case_result.data[0]["id"]

        files_result = (
            sb.table("case_files").select("id, file_name")
            .eq("case_id", case_uuid).eq("file_category", "log").execute()
        )

        results = []
        for f in (files_result.data or []):
            events_result = (
                sb.table("events").select("source", count="exact")
                .eq("case_file_id", f["id"]).limit(1).execute()
            )
            if events_result.data:
                matched_plugin = events_result.data[0]["source"]
                event_count = events_result.count or 0
            else:
                matched_plugin = None
                event_count = 0

            results.append({
                "fileId": f["id"],
                "fileName": f["file_name"],
                "matchedPlugin": matched_plugin,
                "eventCount": event_count,
            })
        return results
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")