"""
services/parser_service.py — Parser Integration Service for ForenSync.

Orchestrates log file parsing by:
    1. Detecting which parser plugin to use for a given file
    2. Invoking the parser to get normalized events
    3. Mapping events to TimelineEvent database rows
    4. Managing parse status lifecycle (queued → processing → parsed/failed)

This is the integration layer ONLY. It does not parse logs itself — that
work is done by the existing parser plugins in Backend/parsers/plugins/.

Public API:
    process_upload(filepath, job_id, case_id, log_file_id) -> int
    detect_parser(filename) -> str

Custom Exceptions:
    UnsupportedFileError
    ParserExecutionError
    DatabasePersistenceError
"""

import sys
import os
import traceback
from datetime import datetime, timezone
from flask import current_app
from models import db, LogFile, TimelineEvent


# ────────────────────────────────────────────────────────────────────────── #
# sys.path manipulation for parser imports
# ────────────────────────────────────────────────────────────────────────── #

_PARSERS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "parsers")
)
if _PARSERS_DIR not in sys.path:
    sys.path.insert(0, _PARSERS_DIR)

from plugins.registry import get_plugin


# ────────────────────────────────────────────────────────────────────────── #
# Custom Exceptions
# ────────────────────────────────────────────────────────────────────────── #

class UnsupportedFileError(Exception):
    """Raised when no plugin is registered for the detected source name."""


class ParserExecutionError(Exception):
    """Raised when plugin.parse() raises any exception."""


class DatabasePersistenceError(Exception):
    """Raised when the DB commit for TimelineEvent rows fails."""


# ────────────────────────────────────────────────────────────────────────── #
# Public API
# ────────────────────────────────────────────────────────────────────────── #

def process_upload(
    filepath: str,
    job_id: str,
    case_id: str,
    log_file_id: int,
) -> int:
    """
    Full orchestration of file parsing and event persistence.

    Steps:
        1. Detect parser from filename
        2. Update LogFile.parse_status = "processing"
        3. Invoke parser.parse(filepath)
        4. Map normalized events to TimelineEvent rows
        5. Bulk insert events
        6. Update LogFile.parse_status = "parsed"
        7. Return event count

    Args:
        filepath:     Absolute path to the saved log file
        job_id:       Job ID (e.g. "JOB-AB12CD34")
        case_id:      Case ID foreign key
        log_file_id:  LogFile.id primary key

    Returns:
        Integer count of events persisted

    Raises:
        UnsupportedFileError:       No parser found for this file
        ParserExecutionError:       Parser crashed during parse()
        DatabasePersistenceError:   Database commit failed
    """
    filename = os.path.basename(filepath)

    try:
        # ──────────────────────────────────────────────────────────────────
        # 1. Detect parser
        # ──────────────────────────────────────────────────────────────────
        source_name = detect_parser(filename)
        current_app.logger.info(
            "[PARSER] Detected parser  file=%s  source=%s  job=%s",
            filename, source_name, job_id,
        )

        # ──────────────────────────────────────────────────────────────────
        # 2. Update status to "processing" before calling parse()
        # ──────────────────────────────────────────────────────────────────
        _update_parse_status(log_file_id, "processing")

        # ──────────────────────────────────────────────────────────────────
        # 3. Get plugin instance
        # ──────────────────────────────────────────────────────────────────
        try:
            plugin = get_plugin(source_name)
        except ValueError as e:
            # Registry raised ValueError → no plugin registered
            raise UnsupportedFileError(
                f"No parser plugin registered for source '{source_name}' (file: {filename})"
            ) from e

        # ──────────────────────────────────────────────────────────────────
        # 4. Invoke parser
        # ──────────────────────────────────────────────────────────────────
        current_app.logger.info(
            "[PARSER] Starting parse  file=%s  source=%s  job=%s",
            filepath, source_name, job_id,
        )

        try:
            normalized_events = plugin.parse(filepath)
        except Exception as e:
            current_app.logger.error(
                "[PARSER] Parser crashed  file=%s  job=%s\n%s",
                filepath, job_id, traceback.format_exc(),
            )
            # Set status to "failed" before re-raising
            _update_parse_status(log_file_id, "failed")
            raise ParserExecutionError(
                f"Parser '{source_name}' failed: {str(e)}"
            ) from e

        event_count = len(normalized_events)
        current_app.logger.info(
            "[PARSER] Parse complete  events=%d  file=%s  job=%s",
            event_count, filename, job_id,
        )

        # ──────────────────────────────────────────────────────────────────
        # 5. Map events and persist
        # ──────────────────────────────────────────────────────────────────
        timeline_events = [
            _map_event(event, case_id, log_file_id)
            for event in normalized_events
        ]

        try:
            db.session.add_all(timeline_events)
            db.session.commit()
            current_app.logger.info(
                "[PARSER] Events persisted  count=%d  case=%s  job=%s",
                event_count, case_id, job_id,
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "[PARSER] DB persistence failed  job=%s\n%s",
                job_id, traceback.format_exc(),
            )
            # Set status to "failed" before re-raising
            _update_parse_status(log_file_id, "failed")
            raise DatabasePersistenceError(
                f"Failed to persist {event_count} events: {str(e)}"
            ) from e

        # ──────────────────────────────────────────────────────────────────
        # 6. Update status to "parsed"
        # ──────────────────────────────────────────────────────────────────
        _update_parse_status(log_file_id, "parsed")

        return event_count

    except (UnsupportedFileError, ParserExecutionError, DatabasePersistenceError):
        # Re-raise typed exceptions without wrapping
        raise
    except Exception as e:
        # Catch any unexpected exception and log it
        current_app.logger.error(
            "[PARSER] Unexpected error  job=%s\n%s",
            job_id, traceback.format_exc(),
        )
        # Set status to "failed" if not already set
        try:
            _update_parse_status(log_file_id, "failed")
        except Exception:
            pass  # Don't crash on status update failure
        raise


def detect_parser(filename: str) -> str:
    """
    Map a filename to a parser plugin source name.

    Rules (evaluated in priority order):
        1. .evtx                            → "windows_event_log"
        2. .log + "nginx"                   → "nginx_access"
        3. .log + "auth"                    → "auth_log"
        4. .log + ("syslog" or "linux")     → "linux_syslog"
        5. .log + ("apache" or "access")    → "apache_access"
        6. .log (no keyword match)          → "linux_syslog" (default)
        7. Anything else                    → UnsupportedFileError

    Args:
        filename: Original filename (e.g. "auth_log_sample.log")

    Returns:
        Source name string (e.g. "auth_log")

    Raises:
        UnsupportedFileError: Extension not mapped to any parser
    """
    lower_name = filename.lower()

    # Rule 1: .evtx
    if lower_name.endswith(".evtx"):
        return "windows_event_log"

    # Rules 2-6: .log files with keyword matching
    if lower_name.endswith(".log"):
        # Check nginx BEFORE access to avoid collision
        if "nginx" in lower_name:
            return "nginx_access"
        if "auth" in lower_name:
            return "auth_log"
        if "syslog" in lower_name or "linux" in lower_name:
            return "linux_syslog"
        if "apache" in lower_name or "access" in lower_name:
            return "apache_access"
        # Default fallback for .log files
        return "linux_syslog"

    # Rule 7: No match
    raise UnsupportedFileError(
        f"File extension not supported for parsing: {filename}"
    )


# ────────────────────────────────────────────────────────────────────────── #
# Internal Helpers
# ────────────────────────────────────────────────────────────────────────── #

def _map_event(event: dict, case_id: str, log_file_id: int) -> TimelineEvent:
    """
    Convert a normalized event dict to a TimelineEvent ORM object.

    Field mapping:
        event["timestamp"]  → timestamp (DateTime) + timestamp_str (str)
        event["source"]     → source
        event["host"]       → host
        event["actor"]      → actor
        event["action"]     → action + event_type
        event["object"]     → object
        event["result"]     → result
        result + action     → severity (via _map_severity)
        actor + action + object → description
        event["raw_log"]    → raw_log + raw_log_hash

    Args:
        event:       Normalized event dict from parser
        case_id:     Foreign key to cases table
        log_file_id: Foreign key to log_files table

    Returns:
        TimelineEvent instance (not yet committed)
    """
    import hashlib
    
    timestamp_str = event.get("timestamp", "unknown")
    timestamp_dt = _parse_timestamp(timestamp_str)

    action = event.get("action", "unknown")
    result = event.get("result", "unknown")
    
    severity = _map_severity(result, action)

    actor = event.get("actor", "unknown")
    object_ = event.get("object", "unknown")
    
    description = _build_description(actor, action, object_)
    
    raw_log = event.get("raw_log", "")
    raw_log_hash = hashlib.sha256(raw_log.encode('utf-8')).hexdigest() if raw_log else None

    return TimelineEvent(
        case_id=case_id,
        log_file_id=log_file_id,
        timestamp=timestamp_dt,
        timestamp_str=timestamp_str if timestamp_str != "unknown" else None,
        source=event.get("source", "unknown"),
        host=event.get("host", None),
        actor=actor if actor != "unknown" else None,
        action=action if action != "unknown" else None,
        object=object_ if object_ != "unknown" else None,
        result=result if result != "unknown" else None,
        event_type=action,
        severity=severity,
        description=description,
        raw_log=raw_log,
        raw_log_hash=raw_log_hash,
        session_id=None,  # Will be populated by timeline generation
    )


def _map_severity(result: str, action: str) -> str:
    """
    Apply severity mapping rules.

    Rules (evaluated in order, first match wins):
        1. result=="failure" AND ("login" OR "ssh" in action)  → "Critical"
        2. result=="failure"                                   → "Warning"
        3. action in privileged set                            → "Warning"
        4. Default                                             → "Info"

    Args:
        result: Event result (e.g. "failure", "success", "unknown")
        action: Event action (e.g. "ssh_login_failed")

    Returns:
        Severity string: "Critical", "Warning", or "Info"
    """
    result_lower = result.lower()
    action_lower = action.lower()

    # Rule 1: Failed login/ssh → Critical
    if result_lower == "failure":
        if "login" in action_lower or "ssh" in action_lower:
            return "Critical"
        # Rule 2: Any other failure → Warning
        return "Warning"

    # Rule 3: Privileged actions → Warning
    if action_lower in {"root_console_login", "windows_privileged_logon"}:
        return "Warning"

    # Rule 4: Default → Info
    return "Info"


def _build_description(actor: str, action: str, object_: str) -> str:
    """
    Build a human-readable description from event fields.

    Format: "{actor} performed {action} on {object}"

    Args:
        actor:   Who performed the action
        action:  What was done
        object_: Target of the action

    Returns:
        Formatted description string
    """
    # Convert action underscores to spaces for readability
    action_readable = action.replace("_", " ")
    return f"{actor} performed {action_readable} on {object_}"


def _parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO 8601 timestamp string to datetime object.

    Args:
        timestamp_str: ISO 8601 UTC string (e.g. "2005-06-18T02:08:11Z")

    Returns:
        datetime object, or current UTC time if parsing fails
    """
    if timestamp_str == "unknown":
        return datetime.now(timezone.utc)

    try:
        # Try with microseconds first
        if "." in timestamp_str:
            return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        # Try without microseconds
        return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        # Fallback to current time
        current_app.logger.warning(
            "[PARSER] Failed to parse timestamp: %s  (using current time)",
            timestamp_str,
        )
        return datetime.now(timezone.utc)


def _update_parse_status(log_file_id: int, status: str) -> None:
    """
    Update LogFile.parse_status and commit immediately.

    Each status transition is committed separately so the database
    always reflects the true current state even if a later step fails.

    Args:
        log_file_id: Primary key of LogFile row
        status:      New status ("queued", "processing", "parsed", "failed")

    Raises:
        DatabasePersistenceError: If the commit fails
    """
    try:
        log_file = db.session.get(LogFile, log_file_id)
        if log_file:
            log_file.parse_status = status
            db.session.commit()
            current_app.logger.debug(
                "[PARSER] Status updated  log_file_id=%d  status=%s",
                log_file_id, status,
            )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            "[PARSER] Failed to update parse_status  log_file_id=%d  status=%s\n%s",
            log_file_id, status, traceback.format_exc(),
        )
        raise DatabasePersistenceError(
            f"Failed to update parse status to '{status}': {str(e)}"
        ) from e
