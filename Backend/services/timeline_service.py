from collections import defaultdict
from datetime import datetime, timedelta
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError

SESSION_WINDOW_MINUTES = 30


def _fetch_all_rows(sb, table_name, select_fields, case_uuid):
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        result = (
            sb.table(table_name).select(select_fields)
            .eq("case_id", case_uuid)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = result.data or []
        all_rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return all_rows

def _resolve_case_uuid(sb, org_id, case_id):
    org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
    if not org_result.data:
        raise NotFoundError(f"Organization '{org_id}' not found.")
    org_uuid = org_result.data[0]["id"]

    case_result = sb.table("cases").select("id").eq("org_id", org_uuid).eq("case_id", case_id).execute()
    if not case_result.data:
        raise NotFoundError(f"Case '{case_id}' not found.")
    return case_result.data[0]["id"]


def generate_timeline(org_id: str, case_id: str, window_minutes: int = SESSION_WINDOW_MINUTES) -> dict:
    sb = _get_client()
    try:
        case_uuid = _resolve_case_uuid(sb, org_id, case_id)

        events = _fetch_all_rows(sb, "events", "id, actor, host, timestamp", case_uuid)

        timed = [e for e in events if e["timestamp"]]
        untimed_count = len(events) - len(timed)

        # Group by (actor, host) so sessions never mix across different actors
        groups = defaultdict(list)
        for e in timed:
            groups[(e["actor"], e["host"])].append(e)

        session_counter = 0
        updates = []

        for key, group_events in groups.items():
            group_events.sort(key=lambda e: e["timestamp"])
            session_counter += 1
            current_session_id = f"session-{session_counter}"
            last_time = None

            for e in group_events:
                t = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
                if last_time is not None and (t - last_time) > timedelta(minutes=window_minutes):
                    session_counter += 1
                    current_session_id = f"session-{session_counter}"
                updates.append({"id": e["id"], "session_id": current_session_id})
                last_time = t

        BATCH_SIZE = 500
        for i in range(0, len(updates), BATCH_SIZE):
            batch = updates[i:i + BATCH_SIZE]
            sb.table("events").upsert(
                [{"id": u["id"], "session_id": u["session_id"]} for u in batch]
            ).execute()

        return {
            "caseId": case_id,
            "eventsClustered": len(updates),
            "sessionsCreated": session_counter,
            "eventsWithoutTimestamp": untimed_count,
        }

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")


def get_timeline(org_id: str, case_id: str, filters: dict) -> dict:
    sb = _get_client()
    try:
        case_uuid = _resolve_case_uuid(sb, org_id, case_id)

        query = sb.table("events").select("*").eq("case_id", case_uuid)
        for field in ("actor", "host", "source", "action"):
            if filters.get(field):
                query = query.eq(field, filters[field])

        all_events = []
        offset = 0
        page_size = 1000
        while True:
            page_result = query.order("timestamp").range(offset, offset + page_size - 1).execute()
            batch = page_result.data or []
            all_events.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        events = all_events
        
        timed = [e for e in events if e["timestamp"]]
        sources = {e["source"] for e in events}

        session_counts = defaultdict(int)
        for e in events:
            if e.get("session_id"):
                session_counts[e["session_id"]] += 1
        correlated_count = sum(c for c in session_counts.values() if c > 1)

        stats = {
            "totalEvents": len(events),
            "uniqueSources": len(sources),
            "correlatedEvents": correlated_count,
            "correlatedPercent": round((correlated_count / len(events)) * 100, 1) if events else 0,
            "earliestEvent": timed[0]["timestamp"] if timed else None,
            "latestEvent": timed[-1]["timestamp"] if timed else None,
        }

        return {"events": events, "stats": stats}

    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")