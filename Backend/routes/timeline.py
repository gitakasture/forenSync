"""
routes/timeline.py — Timeline Blueprint.

Endpoints:
    POST /api/v1/cases/<case_id>/timeline/generate — Generate timeline with event correlation
    GET  /api/v1/cases/<case_id>/timeline          — Get generated timeline
    GET  /api/v1/cases/<case_id>/timeline/stats    — Get timeline summary statistics
"""

from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from services.timeline_correlation_service import (
    generate_timeline,
    get_timeline,
    get_timeline_stats,
)

timeline_bp = Blueprint("timeline", __name__)


@timeline_bp.post("/cases/<string:case_id>/timeline/generate")
def generate_case_timeline(case_id: str):
    """
    Generate timeline by correlating events into sessions.

    Process:
        1. Verify case exists and files are parsed
        2. Retrieve all parsed events
        3. Sort chronologically
        4. Apply correlation algorithm (actor + host + time window)
        5. Assign session IDs
        6. Persist to database

    Response (200):
        {
            "status": "success",
            "message": "Timeline generated successfully.",
            "data": {
                "caseId": "CASE-1042",
                "eventCount": 250,
                "sessionCount": 18,
                "status": "generated"
            }
        }

    Response (400):
        {
            "status": "error",
            "error": "Bad Request",
            "message": "Case has unparsed files. Complete parsing first."
        }

    Response (404):
        {
            "status": "error",
            "error": "Not Found",
            "message": "Case 'CASE-9999' not found."
        }
    """
    current_app.logger.info(
        "POST /cases/%s/timeline/generate", case_id
    )

    try:
        result = generate_timeline(case_id)

        return success_response(
            data=result,
            message="Timeline generated successfully."
        )

    except ValueError as e:
        # Case not found, no events, or unparsed files
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return error_response(
                message=error_msg,
                status_code=404,
                error="Not Found"
            )
        else:
            return error_response(
                message=error_msg,
                status_code=400,
                error="Bad Request"
            )

    except Exception as e:
        # Unexpected error
        current_app.logger.error(
            "Timeline generation error  case=%s\n%s",
            case_id, str(e), exc_info=True
        )
        return error_response(
            message="Failed to generate timeline.",
            status_code=500,
            error="Internal Server Error"
        )


@timeline_bp.get("/cases/<string:case_id>/timeline")
def retrieve_timeline(case_id: str):
    """
    Retrieve chronologically-ordered timeline with correlated sessions.

    Query Parameters:
        - actor (optional): Filter by actor
        - host (optional): Filter by host
        - source (optional): Filter by source
        - action (optional): Filter by action
        - session_id (optional): Filter by session

    Response (200):
        {
            "status": "success",
            "message": "Timeline retrieved successfully.",
            "data": {
                "caseId": "CASE-1042",
                "eventCount": 42,
                "sessionCount": 8,
                "timeline": [
                    {
                        "id": 1,
                        "timestamp": "2005-06-18 02:08:11",
                        "sessionId": "CASE-1042-S0001",
                        "source": "auth_log",
                        "host": "LabSZ",
                        "actor": "218.188.2.4",
                        "action": "ssh_login_failed",
                        "object": "root",
                        "result": "failure",
                        "severity": "Critical",
                        "description": "218.188.2.4 performed ssh login failed on root",
                        "rawLog": "Jun 18 02:08:11 LabSZ sshd[24363]: Failed password..."
                    },
                    ...
                ]
            }
        }

    Response (404):
        {
            "status": "error",
            "error": "Not Found",
            "message": "Case 'CASE-9999' not found."
        }
    """
    current_app.logger.info(
        "GET /cases/%s/timeline", case_id
    )

    # Parse query parameters for filtering
    filters = {}
    if request.args.get("actor"):
        filters["actor"] = request.args.get("actor")
    if request.args.get("host"):
        filters["host"] = request.args.get("host")
    if request.args.get("source"):
        filters["source"] = request.args.get("source")
    if request.args.get("action"):
        filters["action"] = request.args.get("action")
    if request.args.get("session_id"):
        filters["session_id"] = request.args.get("session_id")

    try:
        timeline_data = get_timeline(case_id, filters=filters if filters else None)

        return success_response(
            data=timeline_data,
            message="Timeline retrieved successfully."
        )

    except ValueError as e:
        # Case not found
        return error_response(
            message=str(e),
            status_code=404,
            error="Not Found"
        )

    except Exception as e:
        # Unexpected error
        current_app.logger.error(
            "Timeline retrieval error  case=%s\n%s",
            case_id, str(e), exc_info=True
        )
        return error_response(
            message="Failed to retrieve timeline.",
            status_code=500,
            error="Internal Server Error"
        )


@timeline_bp.get("/cases/<string:case_id>/timeline/stats")
def retrieve_timeline_stats(case_id: str):
    """
    Get summary statistics for a case's timeline.

    Response (200):
        {
            "status": "success",
            "data": {
                "caseId": "CASE-1042",
                "totalEvents": 42,
                "sessionCount": 8,
                "bySeverity": {
                    "Critical": 12,
                    "Warning": 15,
                    "Info": 15
                },
                "bySource": {
                    "auth_log": 30,
                    "linux_syslog": 12
                },
                "logFilesCount": 2,
                "parseStatus": "timeline_generated"
            }
        }
    """
    current_app.logger.info(
        "GET /cases/%s/timeline/stats", case_id
    )

    try:
        stats = get_timeline_stats(case_id)

        return success_response(
            data=stats,
            message="Timeline statistics retrieved successfully."
        )

    except ValueError as e:
        return error_response(
            message=str(e),
            status_code=404,
            error="Not Found"
        )

    except Exception as e:
        current_app.logger.error(
            "Timeline stats error  case=%s\n%s",
            case_id, str(e), exc_info=True
        )
        return error_response(
            message="Failed to retrieve timeline statistics.",
            status_code=500,
            error="Internal Server Error"
        )
