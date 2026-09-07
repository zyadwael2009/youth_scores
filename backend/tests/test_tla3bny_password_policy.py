"""Account password policy: ≥8 chars with an uppercase letter, a lowercase letter, a
digit, and a special character (enforced on every tla3bny set-password path via the
shared `_validate_password`)."""

import os
import tempfile

import pytest

from app.api.tla3bny._helpers import _validate_password


def test_a_strong_password_is_accepted():
    assert _validate_password("Ab1!xxxx") is None      # 8 chars, all four classes
    assert _validate_password("Str0ng#Pass") is None


@pytest.mark.parametrize("pw,why", [
    (None, "missing"),
    ("", "empty"),
    ("Aa1!aa", "too short (6)"),
    ("abcdef1!", "no uppercase"),
    ("ABCDEF1!", "no lowercase"),
    ("Abcdefg!", "no digit"),
    ("Abcdefg1", "no special"),
    ("A1!" + "a" * 200, "too long"),
])
def test_weak_passwords_are_rejected(pw, why):
    assert _validate_password(pw) is not None, why


# ── end-to-end through the register endpoint ─────────────────────────────────
@pytest.fixture()
def client():
    os.environ.setdefault("FLASK_ENV", "development")
    from app import create_app
    from app.config import DevelopmentConfig
    from app.extensions import db

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
    try:
        app = create_app("development")
        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.engine.dispose()
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _register(c, password):
    return c.post("/api/tla3bny/auth/register", json={
        "name": "Falcons Academy", "username": "falcons",
        "password": password, "phone": "01000000000",
    })


def test_register_rejects_a_weak_password_and_accepts_a_strong_one(client):
    assert _register(client, "weakpass").status_code == 400   # no upper/digit/special
    assert _register(client, "Str0ng#Pass").status_code == 201
