#!/usr/bin/env python3
"""
App factory for Habit Tracker (HabitNow-inspired structure)
Sets up Flask app, configuration, CORS, DB initialization, error handling,
and registers API blueprints (if present).

This refactor is backward compatible with the existing backend/app.py entrypoint.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from flask import Flask, jsonify, render_template
from flask_cors import CORS

# Reuse existing modules to keep functionality
from config import get_config
from database import init_db


def _resolve_paths():
    # Base directory of this file: backend/app/
    here = Path(__file__).resolve().parent
    backend_root = here.parent  # backend/
    templates_dir = backend_root / "templates"
    static_dir = backend_root / "static"
    return str(templates_dir), str(static_dir)


def create_app(config_name: Optional[str] = None) -> Flask:
    templates_dir, static_dir = _resolve_paths()

    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir,
    )

    # Load configuration
    ConfigClass = get_config(config_name)
    app.config.from_object(ConfigClass)

    # CORS
    cors_origins = getattr(ConfigClass, "CORS_ORIGINS", ["*"])
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # Initialize database (uses existing sqlite schema)
    init_db()

    # Expose AI availability in config for blueprints
    try:
        # Lazy check mirrors existing optional AI import pattern
        import ai_service  # noqa: F401
        app.config["AI_ENABLED"] = True
    except Exception:
        app.config["AI_ENABLED"] = False

    # ---------- Error Handling ----------
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({"error": "An unexpected error occurred.", "message": str(e)}), 500

    # ---------- Root and status ----------
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/status")
    def api_status():
        return jsonify({
            "status": "online",
            "ai_enabled": bool(app.config.get("AI_ENABLED", False)),
            "timestamp": datetime.now().isoformat(),
        })

    # ---------- Blueprint registration (safe; only if files exist) ----------
    # Blueprints are optional in this step; they will be added in subsequent iterations.
    def _register_optional_blueprint(import_path: str, bp_name: str):
        try:
            module = __import__(import_path, fromlist=["bp"])  # expects module to expose `bp`
            bp = getattr(module, "bp", None)
            if bp is not None:
                app.register_blueprint(bp)
                app.logger.info(f"Registered blueprint: {bp_name}")
        except Exception as ex:
            # Skip silently to preserve backward compatibility until files are added
            app.logger.debug(f"Blueprint {bp_name} not registered: {ex}")

    # Register available blueprints
    _register_optional_blueprint("app.blueprints.habits", "habits")
    _register_optional_blueprint("app.blueprints.tasks", "tasks")
    _register_optional_blueprint("app.blueprints.stats", "stats")
    _register_optional_blueprint("app.blueprints.ai", "ai")
    _register_optional_blueprint("app.blueprints.migrate", "migrate")

    return app


if __name__ == "__main__":
    # Local run for quick verification
    app = create_app(os.getenv("FLASK_ENV"))
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
