"""The tla3bny /home landing feed (today's matches + recent news) is served from
a short in-process TTL cache, with a no-store request bypassing it — so repeat
hits skip the DB while an admin's live refresh still sees fresh data."""

import os
import tempfile
from datetime import datetime, timezone

import pytest


@pytest.fixture()
def app_db():
    os.environ.setdefault("FLASK_ENV", "development")
    from app import create_app
    from app.config import DevelopmentConfig
    from app.extensions import db
    from app.services import cache

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
    try:
        app = create_app("development")
        with app.app_context():
            db.create_all()
            cache.clear()  # the store is process-global; start clean
            yield app, db
            db.session.remove()
            db.engine.dispose()
    finally:
        cache.clear()
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _seed_today_match(db):
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyMatch,
        Tla3bnySeason, Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    h = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="H")
    a = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="A")
    db.session.add_all([h, a])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    m = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id, home_team_id=h.id,
                     away_team_id=a.id, date=datetime.now(timezone.utc).date(),
                     status="scheduled")
    db.session.add(m)
    db.session.commit()
    return m.id


def test_home_is_cached_and_no_store_bypasses(app_db):
    app, db = app_db
    mid = _seed_today_match(db)
    c = app.test_client()

    first = c.get("/api/tla3bny/home")
    assert first.status_code == 200
    body = first.get_json()
    assert "today_matches" in body and "recent_news" in body
    assert len(body["today_matches"]) == 1

    # Remove the match, then a normal read still returns it (served from cache).
    from app.models import Tla3bnyMatch
    db.session.delete(db.session.get(Tla3bnyMatch, mid))
    db.session.commit()
    cached = c.get("/api/tla3bny/home").get_json()
    assert len(cached["today_matches"]) == 1  # stale-but-fresh-enough, from cache

    # A no-store refresh bypasses the cache and recomputes from the DB.
    fresh = c.get("/api/tla3bny/home", headers={"Cache-Control": "no-store"}).get_json()
    assert len(fresh["today_matches"]) == 0
