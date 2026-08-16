"""
test_timeline_correlation.py — Tests for Timeline Generation & Event Correlation.

Tests verify:
- Chronological ordering
- Session correlation based on actor + host + time window
- NULL timestamp handling
- Deterministic session IDs
- Idempotent generation
- Timeline retrieval and filtering
- API response formats
"""

import pytest
from datetime import datetime, timedelta
from models import db, TimelineEvent, LogFile, Case


class TestTimelineCorrelation:
    """Test event correlation logic."""

    def test_chronological_ordering(self, client, test_case):
        """Events should be ordered chronologically, oldest first."""
        # Create events with different timestamps
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=20),
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="Event 3"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="Event 1"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=10),
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="Event 2"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200

        # Retrieve timeline
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        assert response.status_code == 200
        
        data = response.get_json()["data"]
        timeline = data["timeline"]
        
        assert len(timeline) == 3
        assert timeline[0]["description"] == "Event 1"
        assert timeline[1]["description"] == "Event 2"
        assert timeline[2]["description"] == "Event 3"

    def test_same_actor_host_within_window_same_session(self, client, test_case):
        """Events with same actor+host within 30min window should have same session."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="192.168.1.10",
                action="ssh_login_failed",
                source="auth_log",
                description="Event 1"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=15),
                host="server01",
                actor="192.168.1.10",
                action="ssh_login_failed",
                source="auth_log",
                description="Event 2"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=29),
                host="server01",
                actor="192.168.1.10",
                action="ssh_login_success",
                source="auth_log",
                description="Event 3"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200
        
        data = response.get_json()["data"]
        assert data["sessionCount"] == 1

        # Verify all events have same session ID
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        timeline = response.get_json()["data"]["timeline"]
        
        session_ids = [e["sessionId"] for e in timeline]
        assert len(set(session_ids)) == 1
        assert session_ids[0] == f"{test_case.case_id}-S0000"

    def test_same_actor_host_beyond_window_different_sessions(self, client, test_case):
        """Events beyond 30min window should create new session."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="admin",
                action="login",
                source="test_log",
                description="Event 1"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=31),
                host="server01",
                actor="admin",
                action="login",
                source="test_log",
                description="Event 2"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200
        
        data = response.get_json()["data"]
        assert data["sessionCount"] == 2

        # Verify events have different session IDs
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        timeline = response.get_json()["data"]["timeline"]
        
        assert timeline[0]["sessionId"] == f"{test_case.case_id}-S0000"
        assert timeline[1]["sessionId"] == f"{test_case.case_id}-S0001"

    def test_different_actors_different_sessions(self, client, test_case):
        """Events with different actors should have different sessions."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="User1 login"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=5),
                host="server01",
                actor="user2",
                action="login",
                source="test_log",
                description="User2 login"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200
        
        data = response.get_json()["data"]
        assert data["sessionCount"] == 2

        # Verify different session IDs
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        timeline = response.get_json()["data"]["timeline"]
        
        assert timeline[0]["sessionId"] != timeline[1]["sessionId"]

    def test_different_hosts_different_sessions(self, client, test_case):
        """Events with different hosts should have different sessions."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="admin",
                action="login",
                source="test_log",
                description="Server01 event"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=5),
                host="server02",
                actor="admin",
                action="login",
                source="test_log",
                description="Server02 event"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200
        
        data = response.get_json()["data"]
        assert data["sessionCount"] == 2

        # Verify different session IDs
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        timeline = response.get_json()["data"]["timeline"]
        
        assert timeline[0]["sessionId"] != timeline[1]["sessionId"]

    def test_null_timestamps_handled_correctly(self, client, test_case):
        """Events with NULL timestamps should be in UNKNOWN session."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="Timestamped event"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=None,
                host="server01",
                actor="user1",
                action="unknown",
                source="test_log",
                description="NULL timestamp event 1"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=None,
                host="server02",
                actor="user2",
                action="unknown",
                source="test_log",
                description="NULL timestamp event 2"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200
        
        data = response.get_json()["data"]
        assert data["eventCount"] == 3
        assert data["sessionCount"] == 2  # One for timestamped, one UNKNOWN for both NULL

        # Verify NULL events are last and have UNKNOWN session
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        timeline = response.get_json()["data"]["timeline"]
        
        # Timestamped event first
        assert timeline[0]["description"] == "Timestamped event"
        assert timeline[0]["sessionId"] == f"{test_case.case_id}-S0000"
        
        # NULL timestamp events last
        assert timeline[1]["description"] == "NULL timestamp event 1"
        assert timeline[1]["sessionId"] == f"{test_case.case_id}-UNKNOWN"
        assert timeline[2]["description"] == "NULL timestamp event 2"
        assert timeline[2]["sessionId"] == f"{test_case.case_id}-UNKNOWN"

    def test_deterministic_session_ids(self, client, test_case):
        """Session IDs should be deterministic based on event order."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="Login event 1"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=40),
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="Login event 2"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline first time
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200

        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        timeline_first = response.get_json()["data"]["timeline"]
        session_ids_first = [e["sessionId"] for e in timeline_first]

        # Generate timeline second time (idempotent)
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200

        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        timeline_second = response.get_json()["data"]["timeline"]
        session_ids_second = [e["sessionId"] for e in timeline_second]

        # Session IDs should be identical
        assert session_ids_first == session_ids_second
        assert session_ids_first[0] == f"{test_case.case_id}-S0000"
        assert session_ids_first[1] == f"{test_case.case_id}-S0001"

    def test_idempotent_generation(self, client, test_case):
        """Re-running generate_timeline should not create duplicate events."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        event = TimelineEvent(
            case_id=test_case.case_id,
            log_file_id=log_file.id,
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            host="server01",
            actor="user1",
            action="login",
            source="test_log",
            description="Test event"
        )
        db.session.add(event)
        db.session.commit()

        # Generate timeline
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200
        first_count = response.get_json()["data"]["eventCount"]

        # Generate again
        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 200
        second_count = response.get_json()["data"]["eventCount"]

        # Event count should be same
        assert first_count == second_count == 1

        # Verify in database
        events = TimelineEvent.query.filter_by(case_id=test_case.case_id).all()
        assert len(events) == 1


class TestTimelineRetrieval:
    """Test timeline retrieval and filtering."""

    def test_timeline_retrieval(self, client, test_case):
        """Timeline retrieval should return all correlated events."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                host="server01",
                actor="user1",
                action="login",
                object="system",
                result="success",
                severity="Info",
                source="test_log",
                description="User login"
            )
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")

        # Retrieve timeline
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline")
        assert response.status_code == 200
        
        data = response.get_json()["data"]
        assert data["caseId"] == test_case.case_id
        assert data["eventCount"] == 1
        assert data["sessionCount"] == 1
        assert len(data["timeline"]) == 1
        
        event = data["timeline"][0]
        assert event["host"] == "server01"
        assert event["actor"] == "user1"
        assert event["action"] == "login"
        assert event["object"] == "system"
        assert event["result"] == "success"
        assert event["sessionId"] is not None

    def test_timeline_filtering_by_actor(self, client, test_case):
        """Timeline should support filtering by actor."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="User1 event"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=5),
                host="server01",
                actor="user2",
                action="login",
                source="test_log",
                description="User2 event"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")

        # Filter by actor=user1
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline?actor=user1")
        assert response.status_code == 200
        
        timeline = response.get_json()["data"]["timeline"]
        assert len(timeline) == 1
        assert timeline[0]["actor"] == "user1"

    def test_timeline_filtering_by_host(self, client, test_case):
        """Timeline should support filtering by host."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="user1",
                action="login",
                source="test_log",
                description="Server01 login"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=5),
                host="server02",
                actor="user1",
                action="login",
                source="test_log",
                description="Server02 login"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")

        # Filter by host=server02
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline?host=server02")
        assert response.status_code == 200
        
        timeline = response.get_json()["data"]["timeline"]
        assert len(timeline) == 1
        assert timeline[0]["host"] == "server02"


class TestTimelineStatistics:
    """Test timeline statistics endpoint."""

    def test_timeline_stats(self, client, test_case):
        """Statistics should provide summary information."""
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        base_time = datetime(2024, 1, 1, 10, 0, 0)
        events = [
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time,
                host="server01",
                actor="user1",
                action="ssh_login_failed",
                source="auth_log",
                severity="Critical",
                description="Failed SSH login attempt"
            ),
            TimelineEvent(
                case_id=test_case.case_id,
                log_file_id=log_file.id,
                timestamp=base_time + timedelta(minutes=5),
                host="server01",
                actor="user1",
                action="ssh_login_success",
                source="auth_log",
                severity="Info",
                description="Successful SSH login"
            ),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Generate timeline
        client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")

        # Get stats
        response = client.get(f"/api/v1/cases/{test_case.case_id}/timeline/stats")
        assert response.status_code == 200
        
        stats = response.get_json()["data"]
        assert stats["caseId"] == test_case.case_id
        assert stats["totalEvents"] == 2
        assert stats["sessionCount"] == 1
        assert stats["bySeverity"]["Critical"] == 1
        assert stats["bySeverity"]["Info"] == 1
        assert stats["bySource"]["auth_log"] == 2
        assert stats["parseStatus"] == "timeline_generated"


class TestTimelineErrors:
    """Test error handling."""

    def test_generate_timeline_case_not_found(self, client):
        """Should return 404 for non-existent case."""
        response = client.post("/api/v1/cases/NONEXISTENT/timeline/generate")
        assert response.status_code == 404
        assert "not found" in response.get_json()["message"].lower()

    def test_generate_timeline_no_parsed_files(self, client, test_case):
        """Should return 400 if files haven't been parsed."""
        # Create log file with queued status
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="queued"
        )
        db.session.add(log_file)
        db.session.commit()

        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 400
        assert "unparsed" in response.get_json()["message"].lower()

    def test_generate_timeline_no_events(self, client, test_case):
        """Should return 400 if no events exist."""
        # Create parsed log file but no events
        log_file = LogFile(
            case_id=test_case.case_id,
            filename="test.log",
            file_size=100,
            parse_status="parsed"
        )
        db.session.add(log_file)
        db.session.commit()

        response = client.post(f"/api/v1/cases/{test_case.case_id}/timeline/generate")
        assert response.status_code == 400
        assert "no parsed events" in response.get_json()["message"].lower()

    def test_retrieve_timeline_case_not_found(self, client):
        """Should return 404 for non-existent case."""
        response = client.get("/api/v1/cases/NONEXISTENT/timeline")
        assert response.status_code == 404

    def test_retrieve_stats_case_not_found(self, client):
        """Should return 404 for non-existent case."""
        response = client.get("/api/v1/cases/NONEXISTENT/timeline/stats")
        assert response.status_code == 404
