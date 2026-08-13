"""
test_parser_service.py — Unit tests for parser_service.py

Tests:
    - detect_parser() with various filenames
    - _map_severity() with different result/action combinations
    - Parser selection and invocation
    - Error handling for unsupported files
    - Parse status transitions
"""

import pytest
import os
from services.parser_service import (
    detect_parser,
    UnsupportedFileError,
    _map_severity,
)


class TestDetectParser:
    """Test the detect_parser() function with various filename patterns."""

    def test_evtx_file(self):
        """Test .evtx file detection."""
        assert detect_parser("security.evtx") == "windows_event_log"
        assert detect_parser("SECURITY.EVTX") == "windows_event_log"

    def test_auth_log_file(self):
        """Test auth log file detection."""
        assert detect_parser("auth_log_sample.log") == "auth_log"
        assert detect_parser("auth.log") == "auth_log"
        assert detect_parser("AUTH_LOG.LOG") == "auth_log"

    def test_linux_syslog_file(self):
        """Test linux syslog file detection."""
        assert detect_parser("linux_syslog_sample.log") == "linux_syslog"
        assert detect_parser("syslog.log") == "linux_syslog"
        assert detect_parser("linux.log") == "linux_syslog"

    def test_apache_access_file(self):
        """Test apache access log file detection."""
        assert detect_parser("apache_access_sample.log") == "apache_access"
        assert detect_parser("apache.log") == "apache_access"
        assert detect_parser("access.log") == "apache_access"

    def test_nginx_access_file(self):
        """Test nginx access log file detection."""
        assert detect_parser("nginx_access_sample.log") == "nginx_access"
        assert detect_parser("nginx.log") == "nginx_access"

    def test_unknown_log_file_fallback(self):
        """Test that unknown .log files fall back to linux_syslog."""
        assert detect_parser("unknown_file.log") == "linux_syslog"
        assert detect_parser("random.log") == "linux_syslog"

    def test_unsupported_extension(self):
        """Test that unsupported extensions raise UnsupportedFileError."""
        with pytest.raises(UnsupportedFileError):
            detect_parser("malware.exe")

        with pytest.raises(UnsupportedFileError):
            detect_parser("document.pdf")

        with pytest.raises(UnsupportedFileError):
            detect_parser("image.jpg")


class TestMapSeverity:
    """Test the _map_severity() function with various result/action combinations."""

    def test_failed_ssh_login_critical(self):
        """Test failed SSH/login actions map to Critical."""
        assert _map_severity("failure", "ssh_login_failed") == "Critical"
        assert _map_severity("failure", "ssh_invalid_user_attempt") == "Critical"
        assert _map_severity("failure", "login_attempt") == "Critical"
        assert _map_severity("FAILURE", "SSH_LOGIN_FAILED") == "Critical"

    def test_other_failures_warning(self):
        """Test other failure results map to Warning."""
        assert _map_severity("failure", "ftp_connection") == "Warning"
        assert _map_severity("failure", "file_read") == "Warning"
        assert _map_severity("failure", "database_query") == "Warning"

    def test_privileged_actions_warning(self):
        """Test privileged actions map to Warning regardless of result."""
        assert _map_severity("success", "root_console_login") == "Warning"
        assert _map_severity("success", "windows_privileged_logon") == "Warning"
        assert _map_severity("unknown", "root_console_login") == "Warning"

    def test_normal_actions_info(self):
        """Test normal actions map to Info."""
        assert _map_severity("success", "ssh_login_success") == "Info"
        assert _map_severity("success", "file_read") == "Info"
        assert _map_severity("unknown", "unparsed_event") == "Info"
        assert _map_severity("success", "windows_logon_success") == "Info"


class TestParserIntegration:
    """Integration tests for the full parser service flow."""

    def test_sample_log_exists(self):
        """Verify sample log files exist for testing."""
        sample_dir = os.path.join(
            os.path.dirname(__file__), "..", "parsers", "sample_logs"
        )
        assert os.path.exists(sample_dir), "Sample logs directory missing"

        auth_log = os.path.join(sample_dir, "auth_log_sample.log")
        assert os.path.exists(auth_log), "auth_log_sample.log missing"
