"""Regressions for audit round-5 fixes."""

import os
import tempfile

import pytest


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


def test_eligible_players_requires_auth(client):
    # Was public — it exposes a team's full squad + guest-eligible players (names,
    # DOB, photos) and their ban status, so it must require a login now.
    r = client.get("/api/tla3bny/lineups/match/1/team/1/eligible-players")
    assert r.status_code == 401
