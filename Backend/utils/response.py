"""
utils/response.py — Standardized JSON response helpers.

Every endpoint in the app calls success_response() or error_response()
so the React frontend always receives the same envelope shape:

    Success:
        {
            "status":  "success",
            "message": "...",
            "data":    { ... }   ← the actual payload
        }

    Error:
        {
            "status":  "error",
            "error":   "Short Error Name",
            "message": "Human-readable explanation",
            "errors":  [ ... ]   ← optional field-level validation errors
        }

Using helpers instead of raw jsonify() calls in routes means:
  - The shape never drifts between endpoints.
  - The frontend can always look at response.status to branch logic.
  - Adding a field (e.g. a request_id) to every response takes one edit here.
"""

from flask import jsonify, Response


def success_response(
    data: dict | list | None = None,
    message: str = "OK",
    status_code: int = 200,
) -> tuple[Response, int]:
    """
    Return a standardized success JSON response.

    Args:
        data:        The payload to include under the "data" key.
                     Can be a dict, list, or None.
        message:     A short human-readable description of the result.
        status_code: HTTP status code (default 200).

    Returns:
        A (Flask Response, int) tuple ready to be returned from a view.

    Example:
        return success_response(
            data={"caseId": "CASE-1042", "name": "SSH Incident"},
            message="Case created successfully.",
            status_code=201,
        )
    """
    payload = {
        "status": "success",
        "message": message,
        "data": data if data is not None else {},
    }
    return jsonify(payload), status_code


def error_response(
    message: str,
    status_code: int,
    error: str = "Error",
    errors: list | None = None,
) -> tuple[Response, int]:
    """
    Return a standardized error JSON response.

    Args:
        message:     Human-readable explanation of what went wrong.
        status_code: HTTP status code (4xx or 5xx).
        error:       Short error name (e.g. "Not Found", "Validation Error").
        errors:      Optional list of field-level error dicts for form
                     validation failures, e.g.:
                     [{"field": "orgId", "message": "Required."}]

    Returns:
        A (Flask Response, int) tuple ready to be returned from a view.

    Example:
        return error_response(
            message="Organization ID already exists.",
            status_code=409,
            error="Conflict",
        )
    """
    payload: dict = {
        "status": "error",
        "error": error,
        "message": message,
    }
    if errors is not None:
        payload["errors"] = errors

    return jsonify(payload), status_code
