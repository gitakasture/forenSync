"""
config.py — Centralized configuration for ForenSync backend.

All settings are driven by environment variables so the same codebase
runs correctly in development, testing, and production without code changes.
python-dotenv loads a .env file before these classes are evaluated, so
os.getenv() picks up values from that file automatically.

Usage inside create_app():
    app.config.from_object(config_map[config_name])
"""

import os
import logging

# ---------------------------------------------------------------------------
# Base configuration — shared defaults across ALL environments
# ---------------------------------------------------------------------------

class BaseConfig:
    """
    Settings every environment inherits.
    Override any value in a subclass.
    """

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    # SECRET_KEY is used by Flask to cryptographically sign cookies and
    # session data. Must be a long, random, unpredictable string in
    # production. We raise an error if it is missing in non-dev envs
    # (enforced in ProductionConfig below).
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-placeholder")

    # ------------------------------------------------------------------
    # Runtime flags
    # ------------------------------------------------------------------

    # DEBUG enables the Werkzeug interactive debugger and auto-reloader.
    # Always False in base — subclasses opt in.
    DEBUG: bool = False

    # TESTING puts Flask into test mode: exceptions propagate instead of
    # being caught by the error handlers, which makes unit tests cleaner.
    TESTING: bool = False

    # ------------------------------------------------------------------
    # File uploads
    # ------------------------------------------------------------------

    # UPLOAD_FOLDER is the directory where uploaded log files will be saved.
    # We resolve it to an absolute path so it works regardless of the
    # current working directory when the server starts.
    UPLOAD_FOLDER: str = os.path.abspath(
        os.getenv("UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "uploads"))
    )

    # MAX_CONTENT_LENGTH limits the size of incoming request bodies.
    # Flask automatically returns HTTP 413 (Request Entity Too Large) if
    # a request exceeds this value. 50 MB is reasonable for log files.
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB in bytes

    # ALLOWED_EXTENSIONS is a set of file extensions the upload endpoint
    # will accept. Stored as a frozenset for O(1) lookup.
    ALLOWED_EXTENSIONS: frozenset = frozenset({
        "log", "txt", "csv", "json", "xml", "evtx", "pcap"
    })

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    # CORS_ORIGINS is read as a comma-separated string from the environment
    # and split into a list. Flask-CORS uses this list to set
    # Access-Control-Allow-Origin headers.
    # Default: Vite's dev server port.
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    # LOG_LEVEL controls the verbosity of the application logger.
    # In development you want DEBUG; in production WARNING or ERROR.
    LOG_LEVEL: int = logging.DEBUG

    # LOG_FORMAT defines what each log line looks like.
    # %(asctime)s    — timestamp
    # %(levelname)s  — DEBUG / INFO / WARNING / ERROR / CRITICAL
    # %(name)s       — logger name (module path)
    # %(message)s    — the actual log message
    LOG_FORMAT: str = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"

    # LOG_DATE_FORMAT controls how the timestamp is rendered.
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # ------------------------------------------------------------------
    # Application metadata (used by the /health endpoint)
    # ------------------------------------------------------------------

    APP_NAME: str = "ForenSync"
    APP_VERSION: str = "0.1.0"

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @classmethod
    def from_env(cls) -> "BaseConfig":
        """
        Return the correct Config subclass instance based on FLASK_ENV.
        Call this when you need a config object outside of create_app().
        """
        env = os.getenv("FLASK_ENV", "development").lower()
        return config_map.get(env, DevelopmentConfig)


# ---------------------------------------------------------------------------
# Development configuration
# ---------------------------------------------------------------------------

class DevelopmentConfig(BaseConfig):
    """
    Optimised for local development.
    - DEBUG on  → Werkzeug reloader + interactive debugger
    - Verbose logging so you see every request and SQL query (later)
    - Permissive secret key fallback is acceptable here
    """

    DEBUG: bool = True
    LOG_LEVEL: int = logging.DEBUG


# ---------------------------------------------------------------------------
# Testing configuration
# ---------------------------------------------------------------------------

class TestingConfig(BaseConfig):
    """
    Used by pytest and the test suite.
    - TESTING on  → exceptions propagate, no error-handler wrapping
    - DEBUG off   → tests run against production-like error behaviour
    - In-memory / temp upload folder keeps tests isolated
    - Dedicated SECRET_KEY so test tokens never collide with dev tokens
    """

    TESTING: bool = True
    DEBUG: bool = False
    SECRET_KEY: str = "test-secret-key-not-for-production"
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "tests", "uploads")
    LOG_LEVEL: int = logging.WARNING  # keep test output quiet


# ---------------------------------------------------------------------------
# Production configuration
# ---------------------------------------------------------------------------

class ProductionConfig(BaseConfig):
    """
    Hardened for a live deployment.
    - DEBUG off   → no debugger, no auto-reloader
    - SECRET_KEY MUST come from the environment — we raise at startup if missing
    - Logging at WARNING level to reduce noise and log volume
    """

    DEBUG: bool = False
    LOG_LEVEL: int = logging.WARNING

    def __init__(self) -> None:
        # Fail fast: if SECRET_KEY was not set in the environment,
        # refuse to start rather than silently using the insecure placeholder.
        if os.getenv("SECRET_KEY") is None:
            raise EnvironmentError(
                "SECRET_KEY environment variable is required in production. "
                "Set it in your .env file or deployment environment."
            )


# ---------------------------------------------------------------------------
# Config registry — maps FLASK_ENV string → config class
# ---------------------------------------------------------------------------

config_map: dict = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,  # safe fallback
}
