"""
utils/validators.py — Reusable input validation helpers.

Centralizes all request body validation so routes stay thin.
Every validator returns a (is_valid: bool, errors: list[dict]) tuple.

The error dict shape matches what error_response() expects:
    { "field": "fieldName", "message": "Why it failed." }

Usage in a route:
    valid, errs = require_json_fields(request, ["orgId", "userId"])
    if not valid:
        return error_response("Validation failed.", 400, errors=errs)
"""

import os
from flask import Request


# ── JSON body validators ─────────────────────────────────────────────────── #

def require_json_fields(
    req: Request,
    fields: list[str],
) -> tuple[bool, list[dict]]:
    """
    Ensure a JSON request body is present and contains all required fields.

    Args:
        req:    The Flask request object.
        fields: List of field names that must be present and non-empty.

    Returns:
        (True, [])          — all fields present
        (False, [errors])   — list of { field, message } dicts for missing fields
    """
    body = req.get_json(silent=True) or {}
    errors = []

    for field in fields:
        value = body.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append({"field": field, "message": "This field is required."})

    return (len(errors) == 0), errors


def require_form_fields(
    req: Request,
    fields: list[str],
) -> tuple[bool, list[dict]]:
    """
    Ensure a multipart/form-data request contains all required fields.

    Args:
        req:    The Flask request object.
        fields: List of field names that must be present and non-empty.

    Returns:
        (True, [])          — all fields present
        (False, [errors])   — list of { field, message } dicts for missing fields
    """
    errors = []

    for field in fields:
        value = req.form.get(field, "").strip()
        if not value:
            errors.append({"field": field, "message": "This field is required."})

    return (len(errors) == 0), errors


# ── File validators ──────────────────────────────────────────────────────── #

def allowed_file(filename: str, allowed_extensions: frozenset) -> bool:
    """
    Return True if the filename has an allowed extension.

    Args:
        filename:           The original filename from the upload.
        allowed_extensions: Frozenset of allowed extensions (e.g. {"log", "txt"}).

    Returns:
        True if the extension is allowed, False otherwise.

    Note:
        Does NOT validate file content — a file named "malware.log"
        will pass. Content-type sniffing is handled by the parser layer.
    """
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in allowed_extensions


def safe_filename_check(filename: str) -> tuple[bool, str]:
    """
    Basic safety check on an upload filename.

    Rejects:
        - Empty filenames
        - Path traversal attempts (../ or ..)
        - Filenames longer than 255 characters

    Returns:
        (True, "")           — filename is safe
        (False, "reason")    — why it was rejected
    """
    if not filename or not filename.strip():
        return False, "Filename is empty."
    if len(filename) > 255:
        return False, "Filename is too long (max 255 characters)."
    # Reject path separators and traversal sequences
    dangerous = ["..", "/", "\\", "\x00"]
    if any(d in filename for d in dangerous):
        return False, "Filename contains invalid characters."
    return True, ""


# ── String validators ────────────────────────────────────────────────────── #

def validate_id_format(value: str, prefix: str) -> tuple[bool, str]:
    """
    Validate that an ID string matches the expected prefix format.

    Examples:
        validate_id_format("ORG-4410",  "ORG")  → (True,  "")
        validate_id_format("INV-2291",  "INV")  → (True,  "")
        validate_id_format("random",    "ORG")  → (False, "must start with ORG-")

    Args:
        value:  The ID string to validate.
        prefix: The expected prefix (e.g. "ORG", "INV", "HEAD").

    Returns:
        (True, "")           — valid
        (False, "reason")    — why it failed
    """
    expected = f"{prefix}-"
    if not value.startswith(expected):
        return False, f"ID must start with '{expected}' (e.g. {expected}0001)."
    suffix = value[len(expected):]
    if not suffix or not suffix.isalnum():
        return False, f"ID suffix must be alphanumeric (e.g. {expected}0001)."
    return True, ""
