"""
services/timeline_service.py — Timeline Retrieval Service for ForenSync.

Responsible for retrieving and organizing timeline events from parsed log files.
Uses the existing TimelineEvent model and database layer WITHOUT modification.
"""

from flask import current_app
from models import db, TimelineEvent, LogFile, Case
from sqlalchemy import and_


def get_timeline(case_id: str) -> dict:
    """
    Retrieve chronologically-ordered timeline events for a case.
    
    This function queries the ACTUAL TimelineEvent records that were persisted
    by the parser integration when an investigator uploaded log files.
    
    Args:
        case_id: Case identifier (e.g. "CASE-1042")
    
    Returns:
        dict with structure:
        {
            "caseId": str,
            "eventCount": int,
            "parseStatus": str,  # "parsed" | "processing" | "failed" | "queued" | "mixed"
            "timeline": [
                {
                    "id": int,
                    "timestamp": str,
                    "source": str,
                    "eventType": str,
                    "severity": str,
                    "description": str,
                    "rawLog": str
                },
                ...
            ]
        }
    
    Raises:
        ValueError: Case not found or invalid case_id
    """
    # Verify case exists
    case = Case.query.filter_by(case_id=case_id).first()
    if not case:
        raise ValueError(f"Case '{case_id}' not found.")
    
    current_app.logger.info(
        "[TIMELINE] Retrieving timeline  case=%s", case_id
    )
    
    # Check parse status across all log files for this case
    log_files = LogFile.query.filter_by(case_id=case_id).all()
    
    if not log_files:
        # No files uploaded yet
        current_app.logger.debug(
            "[TIMELINE] No log files found  case=%s", case_id
        )
        return {
            "caseId": case_id,
            "eventCount": 0,
            "parseStatus": "queued",
            "timeline": []
        }
    
    # Determine aggregate parse status
    statuses = {lf.parse_status for lf in log_files}
    
    if "failed" in statuses:
        aggregate_status = "failed"
    elif "processing" in statuses or "queued" in statuses:
        aggregate_status = "processing"
    elif len(statuses) == 1 and "parsed" in statuses:
        aggregate_status = "parsed"
    else:
        # Mix of parsed and other statuses
        aggregate_status = "mixed"
    
    # Retrieve all timeline events for this case
    # Ordered chronologically: oldest first (timestamp ASC), with id as tiebreaker
    events = (
        TimelineEvent.query
        .filter_by(case_id=case_id)
        .order_by(TimelineEvent.timestamp.asc(), TimelineEvent.id.asc())
        .all()
    )
    
    event_count = len(events)
    
    current_app.logger.info(
        "[TIMELINE] Retrieved events  case=%s  count=%d  status=%s",
        case_id, event_count, aggregate_status
    )
    
    # Convert to dict using the existing to_dict() method
    timeline = [event.to_dict() for event in events]
    
    return {
        "caseId": case_id,
        "eventCount": event_count,
        "parseStatus": aggregate_status,
        "timeline": timeline
    }


def get_timeline_by_log_file(log_file_id: int) -> dict:
    """
    Retrieve timeline events for a specific log file.
    
    Useful when you want to see events from a single uploaded file
    rather than all files in a case.
    
    Args:
        log_file_id: LogFile primary key
    
    Returns:
        dict with structure:
        {
            "logFileId": int,
            "filename": str,
            "caseId": str,
            "eventCount": int,
            "parseStatus": str,
            "timeline": [...]
        }
    
    Raises:
        ValueError: Log file not found
    """
    # Verify log file exists
    log_file = db.session.get(LogFile, log_file_id)
    if not log_file:
        raise ValueError(f"Log file ID '{log_file_id}' not found.")
    
    current_app.logger.info(
        "[TIMELINE] Retrieving timeline  log_file=%d  case=%s",
        log_file_id, log_file.case_id
    )
    
    # Retrieve events for this specific log file
    events = (
        TimelineEvent.query
        .filter_by(log_file_id=log_file_id)
        .order_by(TimelineEvent.timestamp.asc(), TimelineEvent.id.asc())
        .all()
    )
    
    event_count = len(events)
    
    current_app.logger.info(
        "[TIMELINE] Retrieved events  log_file=%d  count=%d  status=%s",
        log_file_id, event_count, log_file.parse_status
    )
    
    timeline = [event.to_dict() for event in events]
    
    return {
        "logFileId": log_file_id,
        "filename": log_file.filename,
        "caseId": log_file.case_id,
        "eventCount": event_count,
        "parseStatus": log_file.parse_status,
        "timeline": timeline
    }


def get_timeline_stats(case_id: str) -> dict:
    """
    Get summary statistics for a case's timeline.
    
    Args:
        case_id: Case identifier
    
    Returns:
        dict with summary stats:
        {
            "caseId": str,
            "totalEvents": int,
            "bySeverity": {
                "Critical": int,
                "Warning": int,
                "Info": int
            },
            "bySource": {
                "auth_log": int,
                "linux_syslog": int,
                ...
            },
            "logFilesCount": int,
            "parseStatus": str
        }
    
    Raises:
        ValueError: Case not found
    """
    # Verify case exists
    case = Case.query.filter_by(case_id=case_id).first()
    if not case:
        raise ValueError(f"Case '{case_id}' not found.")
    
    # Count events
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
    
    # Log file info
    log_files = LogFile.query.filter_by(case_id=case_id).all()
    log_files_count = len(log_files)
    
    statuses = {lf.parse_status for lf in log_files}
    if "failed" in statuses:
        aggregate_status = "failed"
    elif "processing" in statuses or "queued" in statuses:
        aggregate_status = "processing"
    elif len(statuses) == 1 and "parsed" in statuses:
        aggregate_status = "parsed"
    else:
        aggregate_status = "mixed"
    
    return {
        "caseId": case_id,
        "totalEvents": total_events,
        "bySeverity": severity_counts,
        "bySource": source_counts,
        "logFilesCount": log_files_count,
        "parseStatus": aggregate_status
    }
