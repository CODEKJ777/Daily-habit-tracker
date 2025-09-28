# Flask app entrypoint (delegates to app factory)
#!/usr/bin/env python3
"""
Flask Backend for AI-Powered Habit Tracker
Refactored to use the application factory in backend/app/__init__.py

This preserves the original "python backend/app.py" workflow while enabling
blueprint-based modularization and cleaner architecture.
"""
import os
from app import create_app

app = create_app(os.getenv("FLASK_ENV"))

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
