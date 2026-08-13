"""
routes/upload.py — File upload Blueprint with Parser Integration.

POST /api/v1/upload
    Accepts multipart/form-data log file upload, saves file to storage,
    records LogFile job entry in Database, and triggers parsing.
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, current_app
from models import db, LogFile, Case
from utils.response import success_response, error_response
from utils.validators import allowed_file, safe_filename_check
from services.parser_service import (
    process_upload,
    UnsupportedFileError,
    ParserExecutionError,
    DatabasePersistenceError,
)

upload_bp = Blueprint("upload", __name__)


@upload_bp.post("/upload")
def upload_file():
    """
    Accept log file upload, save file, and write log metadata record to Database.
    """
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

    is_safe, reason = safe_filename_check(uploaded.filename)
    if not is_safe:
        return error_response(
            message=f"Invalid filename: {reason}",
            status_code=400,
            error="Bad Request",
        )

    allowed = current_app.config.get("ALLOWED_EXTENSIONS", frozenset())
    if not allowed_file(uploaded.filename, allowed):
        return error_response(
            message=f"File type not allowed. Accepted extensions: {', '.join(sorted(allowed))}.",
            status_code=415,
            error="Unsupported Media Type",
        )

    safe_name = secure_filename(uploaded.filename)
    job_id = f"JOB-{uuid.uuid4().hex[:8].upper()}"
    stored_filename = f"{job_id}_{safe_name}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_filename)

    uploaded.save(save_path)
    file_size = os.path.getsize(save_path)

    case_id = request.form.get("caseId", "CASE-1042")

    # Persist log file entry into Database
    log_file = LogFile(
        filename=uploaded.filename,
        stored_filename=stored_filename,
        file_size=file_size,
        job_id=job_id,
        parse_status="queued",
        case_id=case_id,
    )
    db.session.add(log_file)
    db.session.commit()

    current_app.logger.info(
        "Upload saved to DB: filename=%s size=%d bytes caseId=%s jobId=%s",
        uploaded.filename,
        file_size,
        case_id,
        job_id,
    )

    # ──────────────────────────────────────────────────────────────────────
    # Parser Integration: Trigger parsing synchronously
    # ──────────────────────────────────────────────────────────────────────
    try:
        event_count = process_upload(
            filepath=save_path,
            job_id=job_id,
            case_id=case_id,
            log_file_id=log_file.id,
        )

        return success_response(
            data={
                "filename":    uploaded.filename,
                "size":        file_size,
                "caseId":      case_id,
                "jobId":       job_id,
                "parseStatus": "parsed",
                "eventCount":  event_count,
            },
            message="File parsed successfully.",
            status_code=200,
        )

    except UnsupportedFileError as e:
        return error_response(
            message=str(e),
            status_code=422,
            error="Unsupported File",
        )

    except ParserExecutionError as e:
        return error_response(
            message=str(e),
            status_code=500,
            error="Parser Error",
        )

    except DatabasePersistenceError as e:
        return error_response(
            message=str(e),
            status_code=500,
            error="Database Error",
        )
