"""Account password policy: deliberately simple so academy staff don't forget it —
at least 4 characters, letters or digits or both, no complexity requirement (enforced
on every tla3bny set-password path via the shared `_validate_password`)."""

import os
import tempfile

import pytest

from app.api.tla3bny._helpers import _validate_password


def test_a_simple_password_is_accepted():
    assert _validate_password("1234") is None          # a 4-digit PIN
    assert _validate_password("ahmed") is None         # letters only
    assert _validate_password("ali2024") is None       # letters + digits
    assert _validate_password("Str0ng#Pass") is None   # a complex one still works


@pytest.mark.parametrize("pw,why", [
    (None, "missing"),
    ("", "empty"),
    ("abc", "too short (3)"),
    ("12", "too short (2)"),
    ("a" * 200, "too long"),
])
def test_bad_passwords_are_rejected(pw, why):
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


def test_register_rejects_a_too_short_password_and_accepts_a_simple_one(client):
    assert _register(client, "abc").status_code == 400        # under 4 characters
    assert _register(client, "1234").status_code == 201       # a simple 4-digit PIN
