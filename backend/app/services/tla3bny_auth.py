"""tla3bny authentication — the LeagueHub subdomain's own login.

Kept deliberately separate from the youthscores admin auth (`services.auth`):
the subdomain (tla3bny.youthscores.org) uses *this* login (academy self-register
+ approval, plus the league super admin), while the main site keeps its own.
Both happen to use the same signed-token mechanism (itsdangerous + SECRET_KEY),
so no extra dependency is needed, but the tokens carry a different salt and
resolve against the `tla3bny_users` table — a youthscores admin token is not
valid here, and vice versa.
"""

from __future__ import annotations

from functools import wraps

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import db
from app.models import Tla3bnyUser

TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
_SALT = "tla3bny-auth-v1"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=_SALT)


def generate_token(user: Tla3bnyUser) -> str:
    return _serializer().dumps(
        {"uid": user.id, "role": user.role, "status": user.status}
    )


def verify_token(token: str) -> Tla3bnyUser | None:
    try:
        data = _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return db.session.get(Tla3bnyUser, data.get("uid"))


def _bearer_token() -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip() or None
    return None


def current_user() -> Tla3bnyUser | None:
    """The signed-in tla3bny account for this request, or None. Cached on g."""
    if "tla3bny_user" in g:
        return g.tla3bny_user
    token = _bearer_token()
    g.tla3bny_user = verify_token(token) if token else None
    return g.tla3bny_user


def public_user(user: Tla3bnyUser) -> dict:
    return user.to_dict()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles: str):
    """Require a signed-in tla3bny account whose role is in `roles`."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error": "unauthorized"}), 401
            if user.role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def approved_academy_required(fn):
    """Require an academy account that has been approved."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "unauthorized"}), 401
        if user.role != "academy":
            return jsonify({"error": "Academy account required"}), 403
        if user.status != "approved":
            return jsonify({"error": "Account not approved yet"}), 403
        return fn(*args, **kwargs)

    return wrapper
