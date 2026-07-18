"""
app.py — Flask Application Factory for ForenSync.

create_app() is the single entry point that builds and returns a fully
configured Flask application instance. Nothing is initialized at module
import time — this makes the app testable and environment-agnostic.

Order of operations inside create_app():
    1. Load .env file via python-dotenv
    2. Create the Flask instance
    3. Apply the correct Config object
    4. Ensure the uploads directory exists
    5. Configure logging
    6. Initialize Flask-CORS
    7. Register Blueprints
    8. Register global error handlers
"""

import os
import logging
import traceback

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from config import config_map


def create_app(config_name: str = "default") -> Flask:
    """
    Application Factory.

    Args:
        config_name: One of "development", "testing", "production", "default".
                     Resolved against config_map in config.py.

    Returns:
        A fully initialised Flask application instance.
    """

    # ------------------------------------------------------------------ #
    # 1. Load environment variables from .env
    #    load_dotenv() looks for a .env file next to this file.
    #    If the file is absent it does nothing — no crash.
    # ------------------------------------------------------------------ #
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    # ------------------------------------------------------------------ #
    # 2. Create the Flask instance
    #    __name__ tells Flask where to find templates and static files
    #    relative to this file's location.
    # ------------------------------------------------------------------ #
    app = Flask(__name__)

    # ------------------------------------------------------------------ #
    # 3. Load configuration
    #    config_map maps the config_name string to a Config class.
    #    from_object() copies class attributes into app.config.
    # ------------------------------------------------------------------ #
    cfg_class = config_map.get(config_name, config_map["default"])
    app.config.from_object(cfg_class)

    # ------------------------------------------------------------------ #
    # 4. Ensure the uploads directory exists
    #    We create it here so the rest of the app can assume it is present.
    # ------------------------------------------------------------------ #
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ------------------------------------------------------------------ #
    # 5. Configure logging
    # ------------------------------------------------------------------ #
    _configure_logging(app)

    # ------------------------------------------------------------------ #
    # 6. Initialise Flask-CORS
    #    Origins, methods, and headers are all driven by config/env vars.
    # ------------------------------------------------------------------ #
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        supports_credentials=False,
    )

    app.logger.info(
        "CORS enabled for origins: %s", app.config["CORS_ORIGINS"]
    )

    # ------------------------------------------------------------------ #
    # 7. Register Blueprints
    #    Each blueprint lives in its own file under routes/.
    #    All routes are versioned under /api/v1/.
    # ------------------------------------------------------------------ #
    _register_blueprints(app)

    # ------------------------------------------------------------------ #
    # 8. Register global error handlers
    # ------------------------------------------------------------------ #
    _register_error_handlers(app)

    app.logger.info(
        "ForenSync backend started  env=%s  debug=%s",
        config_name,
        app.config["DEBUG"],
    )

    return app


# ────────────────────────────────────────────────────────────────────────── #
# Logging setup
# ────────────────────────────────────────────────────────────────────────── #

def _configure_logging(app: Flask) -> None:
    """
    Replace Flask's default handler with one that uses our format and level.

    We attach a StreamHandler (stdout) so logs appear in the terminal and
    are captured by process managers (Docker, systemd, gunicorn) without
    any extra configuration.
    """
    log_level = app.config.get("LOG_LEVEL", logging.DEBUG)
    log_format = app.config.get("LOG_FORMAT")
    date_format = app.config.get("LOG_DATE_FORMAT")

    # Remove any handlers Flask added before we configure ours
    app.logger.handlers.clear()
    app.logger.propagate = False

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)


# ────────────────────────────────────────────────────────────────────────── #
# Blueprint registration
# ────────────────────────────────────────────────────────────────────────── #

def _register_blueprints(app: Flask) -> None:
    """
    Import and register every Blueprint with the app.

    To add a new feature area:
        1. Create routes/my_feature.py and define a Blueprint there.
        2. Import and register it here — nothing else needs to change.
    """
    from routes.health import health_bp
    from routes.upload import upload_bp
    from routes.auth import auth_bp
    from routes.cases import cases_bp
    from routes.plugins import plugins_bp
    from routes.settings import settings_bp

    app.register_blueprint(health_bp,   url_prefix="/api/v1")
    app.register_blueprint(upload_bp,   url_prefix="/api/v1")
    app.register_blueprint(auth_bp,     url_prefix="/api/v1")
    app.register_blueprint(cases_bp,    url_prefix="/api/v1")
    app.register_blueprint(plugins_bp,  url_prefix="/api/v1")
    app.register_blueprint(settings_bp, url_prefix="/api/v1")

    app.logger.debug(
        "Blueprints registered: health, upload, auth, cases, plugins, settings"
    )


# ────────────────────────────────────────────────────────────────────────── #
# Global error handlers
# ────────────────────────────────────────────────────────────────────────── #

def _register_error_handlers(app: Flask) -> None:
    """
    Catch all standard HTTP errors and any unhandled Python exceptions,
    then return a consistent JSON payload so the React frontend never
    receives an HTML error page.

    All responses use error_response() from utils/response.py so the
    shape is guaranteed to match every other error in the API.
    """
    # Import here to avoid circular import at module level
    from utils.response import error_response

    is_dev = app.config.get("DEBUG", False)

    @app.errorhandler(400)
    def bad_request(e):
        return error_response(str(e.description), 400, error="Bad Request")

    @app.errorhandler(404)
    def not_found(e):
        return error_response("The requested resource does not exist.", 404, error="Not Found")

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error_response(str(e.description), 405, error="Method Not Allowed")

    @app.errorhandler(413)
    def request_too_large(e):
        return error_response(
            "The uploaded file exceeds the 50 MB size limit.",
            413,
            error="Payload Too Large",
        )

    @app.errorhandler(422)
    def unprocessable(e):
        return error_response(str(e.description), 422, error="Unprocessable Entity")

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("HTTP 500: %s", str(e))
        return error_response("An unexpected error occurred.", 500, error="Internal Server Error")

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        app.logger.error("Unhandled exception:\n%s", traceback.format_exc())
        # Surface the real message in dev; hide it in production
        message = str(e) if is_dev else "An unexpected error occurred."
        return error_response(message, 500, error="Internal Server Error")
