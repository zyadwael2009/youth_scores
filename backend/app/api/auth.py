"""Login and current-user endpoints for the admin panel."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, limiter
from app.models import AdminUser
from app.services import auth

auth_bp = Blueprint("auth", __name__)

# One-time hash so a missing/inactive user still costs one KDF pass on login:
# equal timing means the response can't be used to enumerate valid usernames.
_DUMMY_HASH = generate_password_hash("timing-equalizer")
_MAX_PW_LEN = 128  # cap before hashing — a multi-MB password would pin a worker


@auth_bp.post("/api/auth/login")
@limiter.limit("10 per minute")
def login():
    j = request.get_json(silent=True) or {}
    username = (j.get("username") or "").strip()
    password = j.get("password") or ""

    user = AdminUser.query.filter_by(username=username).first()
    active = bool(user and user.is_active)
    # Always run exactly one password hash (real user or dummy), so a missing or
    # inactive account isn't given away by a faster response. Same 401 body either
    # way. An over-long password is rejected without hashing.
    if len(password) > _MAX_PW_LEN:
        ok = False
    elif active:
        ok = user.check_password(password)
    else:
        check_password_hash(_DUMMY_HASH, password)  # constant work; result unused
        ok = False
    if not ok:
        return jsonify({"error": "اسم المستخدم أو كلمة المرور غير صحيحة"}), 401

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"token": auth.generate_token(user), "user": auth.public_user(user)})


@auth_bp.get("/api/auth/me")
@auth.login_required
def me():
    user = auth.current_admin()
    if user is None:  # reached only via the master key, which has no user
        return jsonify({"user": None})
    return jsonify({"user": auth.public_user(user)})
