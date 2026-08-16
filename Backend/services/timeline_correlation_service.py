"""
services/timeline_correlation_service.py — Timeline Generation & Event Correlation.

Responsible for:
    1. Retrieving parsed events for a case
    2. Sorting events chronologically
    3. Correlating events into sessions based on actor, host, and temporal proximity
    4. Assigning session IDs to events
    5. Persisting correlation results
    6. Providing timeline data for visualization

Correlation Algorithm:
    Events belong to the same session when:
    - actor is the same
    - host is the same
    - timestamps are within a configurable rolling time window

Public API:
    generate_timeline(case_id) -> dict
    get_timeline(case_id, filters=None) -> dict
"""

import uuid
import traceback
from datetime import timedelta
from flask import current_app
from models import db, TimelineEvent, LogFile, Case
from sqlalchemy import and_, or_


def generate_timeline(case_id: str) -> dict:
    """
    Generate timeline by correlating events into sessions.

    Process:
        1. Verify case exists and has parsed events
        2. Retrieve all events for the case
        3. Sort chronologically (NULL timestamps last)
        4. Apply correlation algorithm to group events into sessions
        5. Assign deterministic session IDs
        6. Persist session_id values to database
        7. Return summary

    Args:
        case_id: Case identifier (e.g. "CASE-1042")

    Returns:
        dict with structure:
        {
            "caseId": str,
            "eventCount": int,
            "sessionCount": int,
            "status": "generated"
        }

    Raises:
        ValueError: Case not found, no events, or parsing incomplete
    """
    # Verify case exists
    case = Case.query.filter_by(case_id=case_id).first()
    if not case:
        raise ValueError(f"Case '{case_id}' not found.")

    current_app.logger.info(
        "[TIMELINE] Starting timeline generation  case=%s", case_id
    )

    # Check if all log files have been parsed
    log_files = LogFile.query.filter_by(case_id=case_id).all()
    if not log_files:
        raise ValueError(f"Case '{case_id}' has no uploaded files.")

    unparsed = [lf for lf in log_files if lf.parse_status != "parsed"]
    if unparsed:
        raise ValueError(
            f"Case '{case_id}' has {len(unparsed)} unparsed files. "
            "Complete parsing before generating timeline."
        )

    # Retrieve all events for this case
    events = TimelineEvent.query.filter_by(case_id=case_id).all()
    if not events:
        raise ValueError(f"Case '{case_id}' has no parsed events.")

    current_app.logger.info(
        "[TIMELINE] Retrieved events  case=%s  count=%d",
        case_id, len(events)
    )

    # Sort events: timestamped events first (chronologically), then NULL timestamps
    timestamped_events = [e for e in events if e.timestamp is not None]
    null_timestamp_events = [e for e in events if e.timestamp is None]

    timestamped_events.sort(key=lambda e: (e.timestamp, e.id))

    sorted_events = timestamped_events + null_timestamp_events

    current_app.logger.info(
        "[TIMELINE] Sorted events  timestamped=%d  null_timestamp=%d",
        len(timestamped_events), len(null_timestamp_events)
    )

    # Apply correlation algorithm
    sessions = _correlate_events(sorted_events, case_id)

    current_app.logger.info(
        "[TIMELINE] Correlation complete  case=%s  sessions=%d",
        case_id, len(sessions)
    )

    # Persist session IDs
    _persist_session_ids(sessions)

    current_app.logger.info(
        "[TIMELINE] Timeline generation complete  case=%s  events=%d  sessions=%d",
        case_id, len(events), len(sessions)
    )

    return {
        "caseId": case_id,
        "eventCount": len(events),
        "sessionCount": len(sessions),
        "status": "generated"
    }


def get_timeline(case_id: str, filters: dict = None) -> dict:
    """
    Retrieve generated timeline with optional filtering.

    Args:
        case_id: Case identifier
        filters: Optional dict with keys: actor, host, source, action, session_id

    Returns:
        dict with structure:
        {
            "caseId": str,
            "eventCount": int,
            "sessionCount": int,
            "timeline": [
                {
                    "id": int,
                    "timestamp": str,
                    "sessionId": str,
                    "source": str,
                    "host": str,
                    "actor": str,
                    "action": str,
                    "object": str,
                    "result": str,
                    "severity": str,
                    "description": str,
                    "rawLog": str
                },
                ...
            ]
        }

    Raises:
        ValueError: Case not found
    """
    # Verify case exists
    case = Case.query.filter_by(case_id=case_id).first()
    if not case:
        raise ValueError(f"Case '{case_id}' not found.")

    current_app.logger.info(
        "[TIMELINE] Retrieving timeline  case=%s  filters=%s",
        case_id, filters
    )

    # Build query with optional filters
    query = TimelineEvent.query.filter_by(case_id=case_id)

    if filters:
        if filters.get("actor"):
            query = query.filter(TimelineEvent.actor == filters["actor"])
        if filters.get("host"):
            query = query.filter(TimelineEvent.host == filters["host"])
        if filters.get("source"):
            query = query.filter(TimelineEvent.source == filters["source"])
        if filters.get("action"):
            query = query.filter(TimelineEvent.action == filters["action"])
        if filters.get("session_id"):
            query = query.filter(TimelineEvent.session_id == filters["session_id"])

    # Retrieve and sort: timestamped first, then NULL
    all_events = query.all()

    timestamped = [e for e in all_events if e.timestamp is not None]
    null_timestamp = [e for e in all_events if e.timestamp is None]

    timestamped.sort(key=lambda e: (e.timestamp, e.id))

    sorted_events = timestamped + null_timestamp

    # Count unique sessions
    session_ids = set(e.session_id for e in sorted_events if e.session_id)

    current_app.logger.info(
        "[TIMELINE] Retrieved timeline  case=%s  events=%d  sessions=%d",
        case_id, len(sorted_events), len(session_ids)
    )

    # Convert to dict
    timeline = [e.to_dict() for e in sorted_events]

    return {
        "caseId": case_id,
        "eventCount": len(timeline),
        "sessionCount": len(session_ids),
        "timeline": timeline
    }


def get_timeline_stats(case_id: str) -> dict:
    """
    Get summary statistics for a case's timeline.

    Args:
        case_id: Case identifier

    Returns:
        dict with summary stats

    Raises:
        ValueError: Case not found
    """
    # Verify case exists
    case = Case.query.filter_by(case_id=case_id).first()
    if not case:
        raise ValueError(f"Case '{case_id}' not found.")

    total_events = TimelineEvent.query.filter_by(case_id=case_id).count()

    # Count by severity
    severity_counts = {}
    for severity in ["Critical", "Warning", "Info"]:
        count = TimelineEvent.query.filter_by(
            case_id=case_id,
            severity=severity
        ).count()
        severity_counts[severity] = count

    # Count by source
    sources = db.session.query(TimelineEvent.source).filter_by(
        case_id=case_id
    ).distinct().all()

    source_counts = {}
    for (source,) in sources:
        count = TimelineEvent.query.filter_by(
            case_id=case_id,
            source=source
        ).count()
        source_counts[source] = count

    # Count sessions
    session_count = db.session.query(TimelineEvent.session_id).filter(
        TimelineEvent.case_id == case_id,
        TimelineEvent.session_id.isnot(None)
    ).distinct().count()

    # Check parse status
    log_files = LogFile.query.filter_by(case_id=case_id).all()
    log_files_count = len(log_files)

    statuses = {lf.parse_status for lf in log_files}
    if "failed" in statuses:
        aggregate_status = "failed"
    elif "processing" in statuses or "queued" in statuses:
        aggregate_status = "processing"
    elif len(statuses) == 1 and "parsed" in statuses:
        # Check if timeline has been generated
        if session_count > 0:
            aggregate_status = "timeline_generated"
        else:
            aggregate_status = "parsed"
    else:
        aggregate_status = "mixed"

    return {
        "caseId": case_id,
        "totalEvents": total_events,
        "sessionCount": session_count,
        "bySeverity": severity_counts,
        "bySource": source_counts,
        "logFilesCount": log_files_count,
        "parseStatus": aggregate_status
    }


# ────────────────────────────────────────────────────────────────────────── #
# Internal Correlation Algorithm
# ────────────────────────────────────────────────────────────────────────── #

def _correlate_events(sorted_events: list, case_id: str) -> list:
    """
    Correlate events into sessions using the rolling time window algorithm.

    Correlation rules:
        - Events with NULL timestamps are grouped into a single "unknown" session
        - Timestamped events belong to the same session when:
            * actor is the same (case-sensitive)
            * host is the same (case-sensitive)
            * timestamps are within the configured rolling window

    Args:
        sorted_events: List of TimelineEvent objects, already sorted chronologically
        case_id: Case identifier for session ID generation

    Returns:
        List of session dicts, each containing:
        {
            "session_id": str,
            "events": [TimelineEvent, ...]
        }
    """
    window_minutes = current_app.config.get("TIMELINE_SESSION_WINDOW_MINUTES", 30)
    time_window = timedelta(minutes=window_minutes)

    sessions = []
    current_session = None

    current_app.logger.debug(
        "[TIMELINE] Correlation config  window_minutes=%d", window_minutes
    )

    for event in sorted_events:
        # Handle NULL timestamp events
        if event.timestamp is None:
            # Group all NULL timestamp events into a single session
            if current_session and current_session.get("is_null_session"):
                current_session["events"].append(event)
            else:
                # Start new NULL timestamp session
                if current_session:
                    sessions.append(current_session)

                session_id = _generate_session_id(case_id, len(sessions), is_null=True)
                current_session = {
                    "session_id": session_id,
                    "events": [event],
                    "is_null_session": True
                }
            continue

        # Timestamped events
        # Check if event belongs to current session
        if current_session and not current_session.get("is_null_session"):
            last_event = current_session["events"][-1]

            same_actor = (event.actor == last_event.actor)
            same_host = (event.host == last_event.host)
            within_window = (event.timestamp - last_event.timestamp) <= time_window

            if same_actor and same_host and within_window:
                # Add to current session
                current_session["events"].append(event)
                continue

        # Start new session
        if current_session:
            sessions.append(current_session)

        session_id = _generate_session_id(case_id, len(sessions), is_null=False)
        current_session = {
            "session_id": session_id,
            "events": [event],
            "is_null_session": False
        }

    # Don't forget the last session
    if current_session:
        sessions.append(current_session)

    return sessions


def _generate_session_id(case_id: str, session_index: int, is_null: bool) -> str:
    """
    Generate a deterministic session ID.

    Format:
        - Timestamped sessions: "{case_id}-S{index:04d}"
        - NULL timestamp session: "{case_id}-UNKNOWN"

    Args:
        case_id: Case identifier
        session_index: Zero-based index of the session
        is_null: Whether this is the NULL timestamp session

    Returns:
        Session ID string
    """
    if is_null:
        return f"{case_id}-UNKNOWN"
    else:
        return f"{case_id}-S{session_index:04d}"


def _persist_session_ids(sessions: list) -> None:
    """
    Update TimelineEvent rows with their assigned session_id.

    This operation is idempotent - running it multiple times with the
    same sessions will produce the same result.

    Args:
        sessions: List of session dicts from _correlate_events()

    Raises:
        DatabasePersistenceError: If the commit fails
    """
    try:
        for session in sessions:
            session_id = session["session_id"]
            for event in session["events"]:
                event.session_id = session_id

        db.session.commit()

        current_app.logger.info(
            "[TIMELINE] Session IDs persisted  sessions=%d",
            len(sessions)
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            "[TIMELINE] Failed to persist session IDs\n%s",
            traceback.format_exc()
        )
        raise DatabasePersistenceError(
            f"Failed to persist session IDs: {str(e)}"
        ) from e


class DatabasePersistenceError(Exception):
    """Raised when database commit fails during timeline generation."""
    pass
