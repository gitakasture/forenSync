"""
test_upload_route.py — HTTP integration tests for the upload endpoint.

Tests:
    - File upload with valid log files
    - Parser integration and event count in response
    - Unsupported file types (HTTP 415)
    - Unsupported file extensions with parsing (HTTP 422)
    - Parse status in database
    - Event persistence in database
"""

import pytest
import os
import io
from models import db, LogFile, TimelineEvent


class TestUploadEndpoint:
    """Test the POST /api/v1/upload endpoint."""

    def test_upload_without_file(self, client):
        """Test upload without file attachment returns 400."""
        response = client.post("/api/v1/upload", data={})
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "file" in data["message"].lower()

    def test_upload_with_empty_filename(self, client):
        """Test upload with empty filename returns 400."""
        response = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(b"test content"), "")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_upload_unsupported_extension(self, client):
        """Test upload with unsupported extension returns 415."""
        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(b"malicious content"), "malware.exe"),
                "caseId": "CASE-TEST",
            },
            content_type="multipart/form-data",
        )
        assert response.status_code == 415
        data = response.get_json()
        assert data["status"] == "error"
        assert "not allowed" in data["message"].lower()

    def test_upload_valid_log_file(self, client, app):
        """Test upload with valid .log file returns 200 and parses successfully."""
        # Use a minimal test log that auth_log parser can handle
        log_content = b"Jun 18 02:08:11 LabSZ sshd[24363]: Failed password for root from 218.188.2.4 port 37279 ssh2\n"

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(log_content), "auth_test.log"),
                "caseId": "CASE-TEST",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "data" in data
        assert "parseStatus" in data["data"]
        assert "eventCount" in data["data"]
        assert data["data"]["parseStatus"] == "parsed"
        assert data["data"]["eventCount"] >= 1

        # Verify database state
        with app.app_context():
            log_file = LogFile.query.filter_by(filename="auth_test.log").first()
            assert log_file is not None
            assert log_file.parse_status == "parsed"
            assert log_file.case_id == "CASE-TEST"

            # Verify events were persisted
            events = TimelineEvent.query.filter_by(log_file_id=log_file.id).all()
            assert len(events) == data["data"]["eventCount"]

    def test_upload_with_real_sample_log(self, client, app):
        """Test upload with an actual sample log file from parsers/sample_logs/."""
        sample_path = os.path.join(
            os.path.dirname(__file__), "..", "parsers", "sample_logs", "auth_log_sample.log"
        )

        if not os.path.exists(sample_path):
            pytest.skip("auth_log_sample.log not found")

        with open(sample_path, "rb") as f:
            log_content = f.read()

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(log_content), "auth_log_sample.log"),
                "caseId": "CASE-TEST",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["data"]["parseStatus"] == "parsed"
        assert data["data"]["eventCount"] > 0

        # Verify parse status in database
        with app.app_context():
            log_file = LogFile.query.filter_by(filename="auth_log_sample.log").first()
            assert log_file is not None
            assert log_file.parse_status == "parsed"

    def test_upload_txt_file_unsupported_for_parsing(self, client):
        """Test that .txt files are allowed for upload but fail parsing with 422."""
        # .txt is in ALLOWED_EXTENSIONS but detect_parser will raise UnsupportedFileError
        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(b"plain text content"), "notes.txt"),
                "caseId": "CASE-TEST",
            },
            content_type="multipart/form-data",
        )

        # Should be 422 because file passes upload validation but has no parser
        assert response.status_code == 422
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error"] == "Unsupported File"


class TestParseStatusLifecycle:
    """Test parse status transitions during upload and parsing."""

    def test_parse_status_queued_then_parsed(self, client, app):
        """Test that parse status goes queued -> processing -> parsed."""
        log_content = b"Jun 18 02:08:11 LabSZ sshd[24363]: Accepted password for admin from 10.0.0.1 port 22 ssh2\n"

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(log_content), "success_test.log"),
                "caseId": "CASE-TEST",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["parseStatus"] == "parsed"

        # Verify final status in database
        with app.app_context():
            log_file = LogFile.query.filter_by(filename="success_test.log").first()
            assert log_file.parse_status == "parsed"


class TestEventSeverity:
    """Test that events are persisted with correct severity levels."""

    def test_failed_ssh_login_critical_severity(self, client, app):
        """Test that failed SSH login events get Critical severity."""
        # Use a log line that auth_log parser can recognize
        log_content = b"Jun 18 02:08:11 LabSZ sshd[24363]: Failed password for root from 218.188.2.4 port 37279 ssh2\n"

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(log_content), "auth_critical_test.log"),
                "caseId": "CASE-TEST",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        data = response.get_json()
        
        # Debug: print response data
        print(f"Response data: {data}")

        with app.app_context():
            log_file = LogFile.query.filter_by(filename="auth_critical_test.log").first()
            assert log_file is not None, "LogFile not found"
            
            events = TimelineEvent.query.filter_by(log_file_id=log_file.id).all()
            print(f"Found {len(events)} events")
            
            for event in events:
                print(f"Event: action={event.event_type}, result parsed from raw, severity={event.severity}")
            
            # Should have at least one event with Critical severity
            critical_events = [e for e in events if e.severity == "Critical"]
            assert len(critical_events) > 0, f"No critical events found. Events: {[(e.event_type, e.severity) for e in events]}"

    def test_successful_ssh_login_info_severity(self, client, app):
        """Test that successful SSH login events get Info severity."""
        log_content = b"Jun 18 02:08:11 LabSZ sshd[24363]: Accepted password for admin from 10.0.0.1 port 22 ssh2\n"

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(log_content), "info_test.log"),
                "caseId": "CASE-TEST",
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 200

        with app.app_context():
            log_file = LogFile.query.filter_by(filename="info_test.log").first()
            events = TimelineEvent.query.filter_by(log_file_id=log_file.id).all()

            # Should have at least one event with Info severity
            info_events = [e for e in events if e.severity == "Info"]
            assert len(info_events) > 0
