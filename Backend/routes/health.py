"""
routes/health.py — Health check Blueprint.

GET /api/v1/health
    Returns application status, environment, and version.
    Used by load balancers, uptime monitors, and the React frontend
    to verify the backend is reachable before making real requests.
"""

import os
from flask import Blueprint, current_app
from utils.response import success_response

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """
    Liveness endpoint — always returns HTTP 200 if the server is running.

    Response (200):
        {
            "status":  "success",
            "message": "OK",
            "data": {
                "app":         "ForenSync",
                "version":     "0.1.0",
                "environment": "development"
            }
        }
    """
    return success_response(
        data={
            "app":         current_app.config.get("APP_NAME", "ForenSync"),
            "version":     current_app.config.get("APP_VERSION", "unknown"),
            "environment": os.getenv("FLASK_ENV", "development"),
        },
        message="OK",
    ) 
    
