"""
services/case_service.py — Case creation and listing for ForenSync.

Handles: creating a case, assigning multiple investigators, and
generating the "you've been assigned" notification for each of them.
"""

import logging
from datetime import datetime, timezone
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError
from services.activity_service import log_activity

logger = logging.getLogger(__name__)

PRIORITY_COLOR_MAP = {
    "Critical": "text-red-400",
    "High Priority": "text-red-400",
    "Medium Priority": "text-amber",
    "Low Priority": "text-blue-400",
}


def _resolve_org_uuid(sb, org_id: str) -> str:
    result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
    if not result.data:
        raise NotFoundError(f"Organization '{org_id}' not found.")
    return result.data[0]["id"]


def _generate_case_id(sb, org_uuid: str) -> str:
    # Stub numbering scheme — replace with a real sequence/serial in production
    result = sb.table("cases").select("case_id").eq("org_id", org_uuid).execute()
    count = len(result.data or [])
    return f"CASE-{1041 + count + 1}"


def create_case(
    org_id: str,
    created_by_user_id: str,
    name: str,
    description: str,
    priority: str,
    incident_from: str,
    incident_to: str,
    investigator_ids: list[str],
) -> dict:
    """
    Creates a case, assigns investigators (status='pending'), and
    creates a notification for each assigned investigator.
    """
    sb = _get_client()

    try:
        org_uuid = _resolve_org_uuid(sb, org_id)

        creator_result = (
            sb.table("users")
            .select("id, name")
            .eq("org_id", org_uuid)
            .eq("user_id", created_by_user_id)
            .eq("role", "head")
            .execute()
        )
        if not creator_result.data:
            raise NotFoundError("Creating head not found in this organization.")
        creator_uuid = creator_result.data[0]["id"]
        creator_name = creator_result.data[0]["name"]

        investigators_result = (
            sb.table("users")
            .select("id, user_id, name")
            .eq("org_id", org_uuid)
            .eq("role", "investigator")
            .in_("user_id", investigator_ids)
            .execute()
        )
        found_investigators = investigators_result.data or []
        if len(found_investigators) != len(investigator_ids):
            found_ids = {inv["user_id"] for inv in found_investigators}
            missing = set(investigator_ids) - found_ids
            raise NotFoundError(f"Investigator(s) not found: {', '.join(missing)}")

        case_id = _generate_case_id(sb, org_uuid)

        case_result = (
            sb.table("cases")
            .insert({
                "case_id": case_id,
                "name": name,
                "description": description,
                "priority": priority,
                "status": "Active",
                "incident_from": incident_from or None,
                "incident_to": incident_to or None,
                "org_id": org_uuid,
                "created_by": creator_uuid,
            })
            .execute()
        )
        if not case_result.data:
            raise ServiceError("Case insert returned no data.")
        case_row = case_result.data[0]
        case_uuid = case_row["id"]

        assignment_rows = [
            {"case_id": case_uuid, "user_id": inv["id"], "status": "pending"}
            for inv in found_investigators
        ]
        sb.table("case_investigators").insert(assignment_rows).execute()

        notification_rows = [
            {
                "user_id": inv["id"],
                "text": f"You have been assigned to a new case {case_id} - {name} by {creator_name}.",
                "is_read": False,
                "related_case_id": case_uuid,
            }
            for inv in found_investigators
        ]
        sb.table("notifications").insert(notification_rows).execute()

        logger.info(
            "[CASES] Created  case_id=%s  org_id=%s  investigators=%d",
            case_id, org_id, len(found_investigators),
        )

        log_activity(
            sb, org_uuid, creator_uuid, "case_created",
            f'Case {case_id} "{name}" created by {creator_name}',
            related_case_id=case_uuid,
        )

        return _build_display_case(sb, case_row)

    except APIError as e:
        logger.error("[CASES] Supabase error: %s", e)
        raise ServiceError(f"Database error while creating case: {e.message}")


def _build_display_case(sb, case_row: dict) -> dict:
    assignments = (
        sb.table("case_investigators").select("user_id").eq("case_id", case_row["id"]).execute()
    )
    investigator_uuids = [a["user_id"] for a in (assignments.data or [])]

    initials = []
    if investigator_uuids:
        users_result = sb.table("users").select("id, name").in_("id", investigator_uuids).execute()
        for u in (users_result.data or []):
            parts = u["name"].split()
            initials.append("".join(p[0].upper() for p in parts)[:2])

    last_updated_raw = case_row.get("updated_at") or case_row.get("created_at")
    last_updated = "—"
    if last_updated_raw:
        date_part, time_part = last_updated_raw.split("T")
        last_updated = f"{date_part}\n{time_part[:5]}"

    files_result = sb.table("case_files").select("id").eq("case_id", case_row["id"]).limit(1).execute()
    has_files = len(files_result.data or []) > 0

    return {
        "caseId": case_row["case_id"],
        "name": case_row["name"],
        "description": case_row.get("description", ""),
        "priority": case_row["priority"],
        "priorityColor": PRIORITY_COLOR_MAP.get(case_row["priority"], "text-ash"),
        "investigators": initials[:2],
        "extraInvestigators": max(0, len(initials) - 2),
        "lastUpdated": last_updated,
        "status": case_row["status"],
        "hasFiles": has_files,
    }

def list_cases_for_investigator(org_id: str, investigator_user_id: str) -> list[dict]:
    """Cases this investigator has CONFIRMED — used for their dashboard/case list."""
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)

        inv_result = (
            sb.table("users").select("id").eq("org_id", org_uuid)
            .eq("user_id", investigator_user_id).eq("role", "investigator").execute()
        )
        if not inv_result.data:
            raise NotFoundError("Investigator not found.")
        inv_uuid = inv_result.data[0]["id"]

        assignments = (
            sb.table("case_investigators")
            .select("case_id")
            .eq("user_id", inv_uuid)
            .eq("status", "confirmed")
            .execute()
        )
        case_uuids = [a["case_id"] for a in (assignments.data or [])]
        if not case_uuids:
            return []

        cases_result = sb.table("cases").select("*").in_("id", case_uuids).execute()
        return [_build_display_case(sb, c) for c in (cases_result.data or [])]

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")

def list_cases_for_head(org_id: str, head_user_id: str) -> list[dict]:
    """Cases CREATED by this head — used for head's dashboard/case list."""
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)

        head_result = (
            sb.table("users").select("id").eq("org_id", org_uuid)
            .eq("user_id", head_user_id).eq("role", "head").execute()
        )
        if not head_result.data:
            raise NotFoundError("Head not found.")
        head_uuid = head_result.data[0]["id"]

        cases_result = (
            sb.table("cases").select("*").eq("org_id", org_uuid).eq("created_by", head_uuid).execute()
        )
        return [_build_display_case(sb, c) for c in (cases_result.data or [])]

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def get_case_detail(org_id: str, case_id: str) -> dict:
    """Full case details for the case detail modal."""
    sb = _get_client()
    try:
        org_uuid = _resolve_org_uuid(sb, org_id)

        case_result = (
            sb.table("cases").select("*").eq("org_id", org_uuid).eq("case_id", case_id).execute()
        )
        if not case_result.data:
            raise NotFoundError(f"Case '{case_id}' not found.")
        case_row = case_result.data[0]

        creator = None
        if case_row.get("created_by"):
            creator_result = (
                sb.table("users").select("name, role").eq("id", case_row["created_by"]).execute()
            )
            if creator_result.data:
                creator = creator_result.data[0]

        assignments = (
            sb.table("case_investigators").select("user_id").eq("case_id", case_row["id"]).execute()
        )
        investigator_uuids = [a["user_id"] for a in (assignments.data or [])]

        investigators = []
        if investigator_uuids:
            users_result = (
                sb.table("users").select("id, user_id, name").in_("id", investigator_uuids).execute()
            )
            for u in (users_result.data or []):
                parts = u["name"].split()
                initials = "".join(p[0].upper() for p in parts)[:2]
                investigators.append({"id": u["user_id"], "name": u["name"], "initials": initials})

        created_on_raw = case_row.get("created_at")
        created_on = "—"
        if created_on_raw:
            date_part, time_part = created_on_raw.split("T")
            created_on = f"{date_part} {time_part[:5]}"

        return {
            "caseId": case_row["case_id"],
            "name": case_row["name"],
            "description": case_row.get("description", ""),
            "status": case_row["status"],
            "createdBy": {
                "name": creator["name"] if creator else "Unknown",
                "role": "Head of Team" if creator and creator["role"] == "head" else "Investigator",
            },
            "createdOn": created_on,
            "investigators": investigators,
        }

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


# def list_cases_for_investigator(org_id: str, investigator_user_id: str) -> list[dict]:
#     """Cases this investigator has CONFIRMED — used for their dashboard/case list."""
#     sb = _get_client()
#     try:
#         org_uuid = _resolve_org_uuid(sb, org_id)

#         inv_result = (
#             sb.table("users").select("id").eq("org_id", org_uuid)
#             .eq("user_id", investigator_user_id).eq("role", "investigator").execute()
#         )
#         if not inv_result.data:
#             raise NotFoundError("Investigator not found.")
#         inv_uuid = inv_result.data[0]["id"]

#         assignments = (
#             sb.table("case_investigators")
#             .select("case_id")
#             .eq("user_id", inv_uuid)
#             .eq("status", "confirmed")
#             .execute()
#         )
#         case_uuids = [a["case_id"] for a in (assignments.data or [])]
#         if not case_uuids:
#             return []

#         cases_result = sb.table("cases").select("*").in_("id", case_uuids).execute()
#         return cases_result.data or []

#     except APIError as e:
#         raise ServiceError(f"Database error: {e.message}")