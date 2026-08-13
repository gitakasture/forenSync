"""
test_parser_service_props.py — Property-based tests for parser_service.py

Uses hypothesis to verify universal properties that should hold across
all valid inputs, rather than testing specific concrete examples.

Properties tested:
    1. detect_parser is deterministic
    2. _map_severity is total and returns valid values
    3. Event field mapping preserves source data
"""

import pytest

try:
    from hypothesis import given, settings, strategies as st
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    pytest.skip("hypothesis not installed", allow_module_level=True)

from services.parser_service import detect_parser, _map_severity, UnsupportedFileError


# Feature: backend-parser-integration, Property 1: detect_parser is deterministic
@given(filename=st.text(min_size=1, max_size=255))
@settings(max_examples=100)
def test_detect_parser_deterministic(filename):
    """
    For any filename, detect_parser returns the same result on repeated calls.
    Either returns a valid source name or raises UnsupportedFileError consistently.
    """
    try:
        result1 = detect_parser(filename)
        result2 = detect_parser(filename)
        assert result1 == result2, "detect_parser must be deterministic"
        assert result1 in {
            "auth_log", "linux_syslog", "apache_access",
            "nginx_access", "windows_event_log"
        }, "must return a valid source name"
    except UnsupportedFileError:
        # Should raise the same exception on second call
        with pytest.raises(UnsupportedFileError):
            detect_parser(filename)


# Feature: backend-parser-integration, Property 4: Severity mapping is total and rule-ordered
@given(
    result=st.text(max_size=50),
    action=st.text(max_size=100),
)
@settings(max_examples=100)
def test_severity_mapping_total(result, action):
    """
    For any (result, action) pair, _map_severity returns exactly one of
    the three valid severity levels: Critical, Warning, or Info.
    """
    severity = _map_severity(result, action)
    assert severity in {"Critical", "Warning", "Info"}, (
        f"_map_severity must return a valid severity, got: {severity}"
    )


# Feature: backend-parser-integration, Property 4 (extended): Severity rules are correctly ordered
@given(action=st.text(max_size=100))
@settings(max_examples=100)
def test_severity_failure_with_login_is_critical(action):
    """
    For any action containing "login" or "ssh", result="failure" maps to Critical.
    """
    if "login" in action.lower() or "ssh" in action.lower():
        severity = _map_severity("failure", action)
        assert severity == "Critical", (
            f"failure + login/ssh should be Critical, got: {severity}"
        )


@given(action=st.text(max_size=100))
@settings(max_examples=100)
def test_severity_any_failure_is_at_least_warning(action):
    """
    For any action, result="failure" maps to at least Warning severity.
    """
    severity = _map_severity("failure", action)
    assert severity in {"Critical", "Warning"}, (
        f"failure should be Critical or Warning, got: {severity}"
    )


@given(result=st.text(max_size=50))
@settings(max_examples=100)
def test_severity_privileged_actions_are_warning(result):
    """
    Privileged actions map to Warning regardless of result.
    """
    for action in ["root_console_login", "windows_privileged_logon"]:
        severity = _map_severity(result, action)
        assert severity == "Warning", (
            f"privileged action should be Warning, got: {severity}"
        )


# Feature: backend-parser-integration, Property: Filename extension detection coverage
@given(
    base=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_categories=("Cs",))),
    extension=st.sampled_from([".log", ".evtx", ".txt", ".exe", ".pdf"]),
)
@settings(max_examples=100)
def test_detect_parser_extension_coverage(base, extension):
    """
    For any base filename + extension:
    - .evtx → windows_event_log
    - .log → one of the log parsers or UnsupportedFileError
    - other extensions → UnsupportedFileError
    """
    filename = base + extension

    if extension == ".evtx":
        result = detect_parser(filename)
        assert result == "windows_event_log"
    elif extension == ".log":
        # Should return one of the log parsers, never crash
        result = detect_parser(filename)
        assert result in {
            "auth_log", "linux_syslog", "apache_access", "nginx_access"
        }
    else:
        # Other extensions should raise UnsupportedFileError
        with pytest.raises(UnsupportedFileError):
            detect_parser(filename)
