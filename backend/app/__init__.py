import logging
import os

from flask import Flask, abort, request, send_from_directory

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

    # ── serve the exported Next.js site on the same domain as the API ─────────
    # FRONTEND_DIR is the `out/` produced by `next build` (static export).
    # Defaults to ../web/out relative to the repo; override with the env var to
    # point elsewhere, or leave the folder absent on an API-only host.
    frontend_dir = os.environ.get("FRONTEND_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(app.root_path)), "web", "out"
    )
    app.config["FRONTEND_DIR"] = frontend_dir

    def _serve_frontend(path: str):
        """Serve the static export for a browser path.

        The export uses trailingSlash, so /competition/ is the file
        competition/index.html. Real files (JS, CSS, sw.js, manifest, icons) are
        served as-is; an unmatched path returns the exported 404 page.
        """
        root = app.config["FRONTEND_DIR"]
        if not os.path.isdir(root):
            abort(404)
        if path and os.path.isfile(os.path.join(root, path)):
            return send_from_directory(root, path)
        index = os.path.join(path, "index.html") if path else "index.html"
        if os.path.isfile(os.path.join(root, index)):
            return send_from_directory(root, index)
        if os.path.isfile(os.path.join(root, "404.html")):
            return send_from_directory(root, "404.html"), 404
        abort(404)

    @app.get("/")
    def _frontend_root():
        return _serve_frontend("")

    @app.get("/<path:path>")
    def _frontend_path(path):
        # The API and uploads have their own, more specific routes; guard here so
        # an unknown /api/... path returns a 404 rather than the HTML shell.
        if path.startswith(("api/", "uploads/")):
            abort(404)
        return _serve_frontend(path)

    return app
