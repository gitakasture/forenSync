"""
conftest.py — Pytest configuration and fixtures for ForenSync backend tests.

Provides:
    - app fixture: Flask application in testing mode with in-memory database
    - client fixture: Test client for making HTTP requests
    - test_case fixture: Pre-created test case for timeline tests
    - app_context fixture: Push app context for database operations
"""

import os
import pytest
from datetime import datetime
from app import create_app
from models import db, Organization, User, Case, LogFile, TimelineEvent


@pytest.fixture
def app():
    """
    Create and configure a Flask application for testing.

    - Uses TestingConfig (in-memory SQLite database)
    - Creates all database tables
    - Seeds a test organization and case for foreign key integrity
    """
    test_app = create_app("testing")

    with test_app.app_context():
        # Database is already initialized by create_app via init_db()
        # Seed minimal test data
        _seed_test_data()

    yield test_app

    # Cleanup after tests
    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Return a test client for the app.

    The client can make HTTP requests to the app's endpoints without
    starting a real server.
    """
    return app.test_client()


@pytest.fixture
def test_case(app):
    """
    Return a test case for timeline correlation tests.
    
    This fixture must be used within the app context.
    """
    # Push context to ensure database operations work
    with app.app_context():
        case = Case.query.filter_by(case_id="CASE-TEST").first()
        yield case


@pytest.fixture(autouse=True)
def app_context(app):
    """
    Automatically push the app context for all tests.
    
    This ensures database operations work in test methods.
    """
    with app.app_context():
        yield


def _seed_test_data():
    """
    Seed minimal test data for foreign key integrity.

    Creates:
        - Organization: ORG-TEST
        - User: HEAD-TEST (organization head)
        - Case: CASE-TEST
    """
    # Check if data already exists
    if Organization.query.filter_by(org_id="ORG-TEST").first():
        return

    org = Organization(
        org_id="ORG-TEST",
        name="Test Organization",
        org_head_id="HEAD-TEST",
    )
    db.session.add(org)
    db.session.commit()

    user = User(
        user_id="HEAD-TEST",
        name="Test Head",
        role="head",
        org_id="ORG-TEST",
    )
    db.session.add(user)
    db.session.commit()

    case = Case(
        case_id="CASE-TEST",
        name="Test Case",
        description="Test case for parser integration tests",
        timeframe="Test timeframe",
        status="Active",
        action="Open",
        org_id="ORG-TEST",
    )
    db.session.add(case)
    db.session.commit()
