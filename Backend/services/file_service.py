"""
services/file_service.py — Case file uploads for ForenSync.
Uploads to Supabase Storage bucket 'case-files', records metadata
in the case_files table.
"""

import logging
import uuid
from postgrest.exceptions import APIError
from services.auth_service import _get_client, NotFoundError, ServiceError
from services.activity_service import log_activity

logger = logging.getLogger(__name__)
BUCKET_NAME = "case-files"


def upload_case_files(org_id: str, case_id: str, uploader_user_id: str, log_files: list, other_files: list) -> dict:
    """
    log_files / other_files: list of (filename, file_bytes, content_type) tuples
    """
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        user_result = (
            sb.table("users").select("id, name").eq("org_id", org_uuid).eq("user_id", uploader_user_id).execute()
        )
        if not user_result.data:
            raise NotFoundError("Uploading user not found.")
        uploader_uuid = user_result.data[0]["id"]
        uploader_name = user_result.data[0]["name"]

        case_result = (
            sb.table("cases").select("id").eq("org_id", org_uuid).eq("case_id", case_id).execute()
        )
        if not case_result.data:
            raise NotFoundError(f"Case '{case_id}' not found.")
        case_uuid = case_result.data[0]["id"]

        uploaded_count = 0

        def _upload_group(files, category):
            nonlocal uploaded_count
            for filename, file_bytes, content_type in files:
                unique_name = f"{uuid.uuid4()}_{filename}"
                storage_path = f"{org_id}/{case_id}/{category}/{unique_name}"

                sb.storage.from_(BUCKET_NAME).upload(
                    storage_path, file_bytes,
                    {"content-type": content_type or "application/octet-stream"},
                )

                sb.table("case_files").insert({
                    "case_id": case_uuid,
                    "uploaded_by": uploader_uuid,
                    "file_name": filename,
                    "storage_path": storage_path,
                    "file_category": category,
                    "file_size": len(file_bytes),
                }).execute()
                uploaded_count += 1

        _upload_group(log_files, "log")
        _upload_group(other_files, "other")

        log_activity(
            sb, org_uuid, uploader_uuid, "files_uploaded",
            f"{uploader_name} uploaded {uploaded_count} file(s) to {case_id}",
            related_case_id=case_uuid,
        )

        logger.info("[FILES] Uploaded  case_id=%s  count=%d", case_id, uploaded_count)
        return {"caseId": case_id, "filesUploaded": uploaded_count}

    except APIError as e:
        logger.error("[FILES] Supabase error: %s", e)
        raise ServiceError(f"Database/storage error: {e.message}")

def list_case_files(org_id: str, case_id: str, category: str = None) -> list[dict]:
    sb = _get_client()
    try:
        org_result = sb.table("organizations").select("id").eq("org_id", org_id).execute()
        if not org_result.data:
            raise NotFoundError(f"Organization '{org_id}' not found.")
        org_uuid = org_result.data[0]["id"]

        case_result = sb.table("cases").select("id").eq("org_id", org_uuid).eq("case_id", case_id).execute()
        if not case_result.data:
            raise NotFoundError(f"Case '{case_id}' not found.")
        case_uuid = case_result.data[0]["id"]

        query = sb.table("case_files").select("id, file_name, file_size, file_category, uploaded_at").eq("case_id", case_uuid)
        if category:
            query = query.eq("file_category", category)
        result = query.order("uploaded_at", desc=True).execute()

        return [
            {
                "id": f["id"],
                "fileName": f["file_name"],
                "fileSize": f["file_size"],
                "fileCategory": f["file_category"],
                "uploadedAt": f["uploaded_at"],
            }
            for f in (result.data or [])
        ]
    except APIError as e:
        raise ServiceError(f"Database error: {e.message}")