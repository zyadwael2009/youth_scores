"""The tla3bny read endpoints memoise their build in the in-process compute cache;
a client that asks to bypass (Cache-Control: no-store, what an authed refresh sends)
always recomputes. Verified on get_competition."""

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
            yield app, db
            db.session.remove()
            db.engine.dispose()
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _seed(db):
    from app.models import Tla3bnyCompetition, Tla3bnySeason
    season = Tla3bnySeason(name="2026-2027")
    db.session.add(season)
    db.session.flush()
    comp = Tla3bnyCompetition(name="Old Name", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.commit()
    return comp.id


def test_get_competition_is_cached_and_no_store_bypasses(client):
    app, db = client
    from app.models import Tla3bnyCompetition
    c = app.test_client()
    comp_id = _seed(db)

    # Prime the cache (public request, no token).
    assert c.get(f"/api/tla3bny/competitions/{comp_id}").get_json()["name"] == "Old Name"

    # Change the name underneath the cache.
    db.session.get(Tla3bnyCompetition, comp_id).name = "New Name"
    db.session.commit()

    # A normal public read is still served the cached (old) value…
    assert c.get(f"/api/tla3bny/competitions/{comp_id}").get_json()["name"] == "Old Name"
    # …while a no-store request (an admin's live refresh) recomputes.
    fresh = c.get(f"/api/tla3bny/competitions/{comp_id}",
                  headers={"Cache-Control": "no-store"}).get_json()
    assert fresh["name"] == "New Name"
