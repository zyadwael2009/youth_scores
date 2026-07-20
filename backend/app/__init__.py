import logging
import os

from flask import Flask, request, send_from_directory

from app.config import CONFIGS
from app.extensions import db, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(CONFIGS.get(config_name, CONFIGS["development"]))

    # Make INFO logs (e.g. notification dry-run lines) visible in development;
    # `flask run` otherwise leaves the app logger at WARNING.
    if app.config.get("DEBUG"):
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)

    # Emit Arabic as UTF-8, not \uXXXX escapes.
    app.json.ensure_ascii = False

    # Where uploaded images live (defaults under the instance folder).
    if not app.config.get("UPLOAD_FOLDER"):
        app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    # Registers every mapper before Alembic autogenerate inspects the metadata.
    from app import models  # noqa: F401

    from app.api import api_bp
    from app.api.admin import admin_bp
    from app.api.auth import auth_bp
    from app.api.entry import entry_bp
    from app.api.manage import manage_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(entry_bp)
    app.register_blueprint(manage_bp)

    from app.commands import register_commands

    register_commands(app)

    # CORS for the browser clients (public site + admin panel on other ports).
    @app.before_request
    def _preflight():
        if request.method == "OPTIONS":
            return ("", 204)

    @app.after_request
    def _cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Admin-Key"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
