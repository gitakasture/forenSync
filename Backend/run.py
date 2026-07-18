"""
run.py — ForenSync backend entry point.

Usage:
    python run.py              # direct execution
    flask run                  # via Flask CLI (requires FLASK_APP=run.py)
"""

import os
from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_RUN_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_RUN_PORT", 5000)),
        debug=app.config.get("DEBUG", True),
    )
