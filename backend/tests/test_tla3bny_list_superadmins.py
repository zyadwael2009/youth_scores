"""scripts.list_tla3bny_superadmins.list_admins — the confirm-it-exists helper."""

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


def test_lists_admins_and_excludes_academy_accounts(app_db):
    db = app_db
    from app.models import Tla3bnyUser
    from scripts.list_tla3bny_superadmins import list_admins

    db.session.add_all([
        Tla3bnyUser(username="zantac", role="super_admin", status="active", password_hash="x"),
        Tla3bnyUser(username="org1", role="competition_admin", status="active", password_hash="x"),
        Tla3bnyUser(username="acad", role="academy", status="active", password_hash="x", academy_id=None),
    ])
    db.session.commit()

    rows = list_admins()
    usernames = {u.username for u in rows}
    assert usernames == {"zantac", "org1"}          # academy excluded
    assert all(u.role in ("super_admin", "competition_admin") for u in rows)
