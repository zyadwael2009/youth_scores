"""The .ics calendar feeds: a single match ("add to calendar") and a team's
subscribable fixtures feed."""

import os
import tempfile
from datetime import date

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
            yield app.test_client(), db
            db.session.remove()
            db.engine.dispose()
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _seed(db):
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
    h = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="Falcons")
    a = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="Eagles")
    db.session.add_all([h, a])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    timed = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id, home_team_id=h.id,
                         away_team_id=a.id, date=date(2026, 9, 1), time="16:30",
                         venue="Main Pitch", status="scheduled")
    dateless = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id, home_team_id=h.id,
                            away_team_id=a.id, status="scheduled")  # no date
    db.session.add_all([timed, dateless])
    db.session.commit()
    return {"timed": timed.id, "dateless": dateless.id, "home": h.id, "away": a.id}


def test_match_calendar_has_a_vevent_with_kickoff(client):
    c, db = client
    s = _seed(client[1])
    r = c.get(f"/api/tla3bny/matches/{s['timed']}/calendar.ics")
    assert r.status_code == 200
    assert r.mimetype == "text/calendar"
    body = r.get_data(as_text=True)
    assert "BEGIN:VCALENDAR" in body and "BEGIN:VEVENT" in body
    assert "DTSTART:20260901T163000" in body           # floating local kickoff
    assert "DTEND:20260901T180000" in body             # +90 minutes
    assert "LOCATION:Main Pitch" in body
    assert f"UID:t3-match-{s['timed']}@youthscores" in body


def test_match_calendar_without_a_date_is_404(client):
    c, db = client
    s = _seed(client[1])
    assert c.get(f"/api/tla3bny/matches/{s['dateless']}/calendar.ics").status_code == 404


def test_team_fixtures_feed_lists_only_dated_matches(client):
    c, db = client
    s = _seed(client[1])
    r = c.get(f"/api/tla3bny/teams/{s['home']}/fixtures.ics")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    # One dated match for this team → exactly one VEVENT (the dateless one is skipped).
    assert body.count("BEGIN:VEVENT") == 1
    assert "SUMMARY:Falcons × Eagles" in body
