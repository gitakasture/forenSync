"""
routes/upload.py — File upload Blueprint.

POST /api/v1/upload
    Accepts a multipart/form-data file upload.
    Currently returns a realistic mock response (HTTP 200) so the
    React frontend's NewCaseFile.jsx form can complete successfully
    without UI changes.

    When the parser and database are ready, the TODO markers below
    show exactly where each integration point plugs in.
"""

import os
from flask import Blueprint, request, current_app
from utils.response import success_response, error_response
from utils.validators import allowed_file, safe_filename_check, require_form_fields

upload_bp = Blueprint("upload", __name__)


@upload_bp.post("/upload")
def upload_file():
    """
    Accept and (mock) process an uploaded log file.

    Request: multipart/form-data
        file        (required) — the log file binary
        caseId      (optional) — associate upload with an existing case

    Response (200) — mock:
        {
            "status":  "success",
            "message": "File received and queued for processing.",
            "data": {
                "filename":  "auth.log",
                "size":      4096,
                "caseId":    "CASE-1099",
                "jobId":     "JOB-MOCK-001",
                "parseStatus": "queued"
            }
        }

    TODO (database phase):
        - Replace mock caseId lookup with:
            case = CaseService.get_by_id(case_id)
        - Replace mock job creation with:
            job = ParserJobService.create(case_id=case_id, filename=saved_path)
        - Return real job.id instead of "JOB-MOCK-001"

    TODO (parser phase):
        - After saving the file, dispatch to the plugin registry:
            plugin = PluginRegistry.get_active()
            plugin.enqueue(saved_path, job_id=job.id)
    """
    # ── 1. Validate a file was actually attached ─────────────────────── #
    if "file" not in request.files:
        return error_response(
            message="No file attached. Send the file under the 'file' field.",
            status_code=400,
            error="Bad Request",
        )

    uploaded = request.files["file"]

    if not uploaded.filename:
        return error_response(
            message="The attached file has no filename.",
            status_code=400,
            error="Bad Request",
        )

    # ── 2. Safety check the filename ─────────────────────────────────── #
    is_safe, reason = safe_filename_check(uploaded.filename)
    if not is_safe:
        return error_response(
            message=f"Invalid filename: {reason}",
            status_code=400,
            error="Bad Request",
        )

    # ── 3. Check extension is in the allowed list ─────────────────────── #
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", frozenset())
    if not allowed_file(uploaded.filename, allowed):
        return error_response(
            message=(
                f"File type not allowed. Accepted extensions: "
                f"{', '.join(sorted(allowed))}."
            ),
            status_code=415,
            error="Unsupported Media Type",
        )

    # ── 4. (Mock) Save the file ───────────────────────────────────────── #
    # TODO (database + storage phase): replace with real save logic:
    #   from werkzeug.utils import secure_filename
    #   safe_name  = secure_filename(uploaded.filename)
    #   save_path  = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_name)
    #   uploaded.save(save_path)
    #   file_size  = os.path.getsize(save_path)
    #
    # For now we just read the size from the stream without saving.
    uploaded.stream.seek(0, 2)       # seek to end
    file_size = uploaded.stream.tell()
    uploaded.stream.seek(0)          # reset

    case_id = request.form.get("caseId", "CASE-1099")

    current_app.logger.info(
        "Upload received (mock): filename=%s size=%d bytes caseId=%s",
        uploaded.filename,
        file_size,
        case_id,
    )

    # ── 5. Return mock queued-job response ────────────────────────────── #
    # TODO (parser phase): replace "JOB-MOCK-001" with real job.id
    # TODO (parser phase): replace "queued" with real job status from DB
    return success_response(
        data={
            "filename":    uploaded.filename,
            "size":        file_size,
            "caseId":      case_id,
            "jobId":       "JOB-MOCK-001",
            "parseStatus": "queued",
        },
        message="File received and queued for processing.",
        status_code=200,
    )
