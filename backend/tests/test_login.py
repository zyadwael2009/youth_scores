"""Login still authenticates correctly after the constant-work / length-cap
hardening (audit LOW): a valid login succeeds; a wrong password, missing user,
inactive user, and an over-long password all get the same 401.
"""

import os
import tempfile

import pytest

GOOD = "goodpass1"


@pytest.fixture()
def app_ctx():
    os.environ.setdefault("FLASK_ENV", "development")
    from app import create_app
    from app.config import DevelopmentConfig
    from app.extensions import db

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
    app = create_app("development")
    with app.app_context():
        db.create_all()
        from app.models import AdminUser

        active = AdminUser(username="alice", role="editor", is_active=True)
        active.set_password(GOOD)
        gone = AdminUser(username="bob", role="clerk", is_active=False)
        gone.set_password(GOOD)
        db.session.add_all([active, gone])
        db.session.commit()
    try:
        yield app
    finally:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _login(app, username, password):
    return app.test_client().post(
        "/api/auth/login", json={"username": username, "password": password}
    )


def test_valid_login_returns_a_token(app_ctx):
    r = _login(app_ctx, "alice", GOOD)
    assert r.status_code == 200
    assert r.get_json().get("token")


@pytest.mark.parametrize(
    "username,password",
    [
        ("alice", "wrongpass"),      # wrong password
        ("nobody", GOOD),            # missing user
        ("bob", GOOD),               # inactive user, right password
        ("alice", "x" * 5000),       # over-long password (rejected without hashing)
    ],
)
def test_bad_logins_are_401(app_ctx, username, password):
    r = _login(app_ctx, username, password)
    assert r.status_code == 401
    assert "token" not in (r.get_json() or {})
