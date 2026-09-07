"""The create-super-admin script's core (scripts.create_tla3bny_superadmin)."""

import os
import tempfile

import pytest


@pytest.fixture()
def app_db():
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
            yield db
            db.session.remove()
            db.engine.dispose()
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def test_creates_then_promotes_the_same_account(app_db):
    db = app_db
    from app.models import Tla3bnyUser
    from scripts.create_tla3bny_superadmin import create_or_update_superadmin

    user, created = create_or_update_superadmin("BossMan", "Test_1234")
    assert created is True
    assert user.username == "bossman"           # normalized (trim + lowercase)
    assert user.role == "super_admin"
    assert user.status == "active"
    assert user.check_password("Test_1234")

    # Same username again → updates the SAME row (no duplicate) and resets the password.
    user2, created2 = create_or_update_superadmin("bossman", "New_5678")
    assert created2 is False
    assert user2.id == user.id
    assert Tla3bnyUser.query.filter_by(username="bossman").count() == 1
    assert user2.check_password("New_5678")
    assert not user2.check_password("Test_1234")
