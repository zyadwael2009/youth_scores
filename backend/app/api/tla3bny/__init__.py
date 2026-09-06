from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

tla3bny_bp = Blueprint("tla3bny", __name__, url_prefix="/api/tla3bny")


@tla3bny_bp.errorhandler(SQLAlchemyError)
def _tla3bny_db_error(exc):
    """Roll back on any unhandled DB error so a failed write — e.g. an over-long
    value hitting a column's length limit — can't leave the session poisoned for the
    rest of the request. Returns a clean 500 instead of a mid-transaction crash. A
    universal safety net; routes still clip user input up front so the common case is
    a tidy 400/409 rather than a 500."""
    db.session.rollback()
    current_app.logger.exception("tla3bny unhandled DB error")
    return jsonify({"error": "database error"}), 500


@tla3bny_bp.after_request
def _tla3bny_cache(response):
    """Cache public reads; never cache authenticated responses.

    This blueprint serves both the public site (matches, standings, news) and
    authenticated admin/coach actions. A response tied to a token is
    user-specific, so it is marked no-store; anonymous successful GETs get a
    short shared-cache window (live scores stay near-fresh) that lets a CDN or
    the browser answer repeat requests without hitting Railway compute.
    """
    if request.headers.get("Authorization"):
        response.headers.setdefault("Cache-Control", "private, no-store")
    elif request.method == "GET" and response.status_code == 200:
        response.headers.setdefault(
            "Cache-Control", "public, max-age=30, stale-while-revalidate=120"
        )
    return response


from . import auth, academies, teams, players, seasons, categories, competitions, matches, news, ads, stats, fixtures, audit, search, awards, punishments, chat, push  # noqa: E402, F401
