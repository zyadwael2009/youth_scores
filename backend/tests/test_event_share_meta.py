"""Event JSON-LD on match & competition share cards. Google flags a SportsEvent
that lacks startDate + location (a critical Search Console error), so the share-meta
builders attach an ``event`` dict; here we pin that a dated match / a competition
with a season emit the required fields, and a TBD (dateless) match emits none."""

import os
import tempfile
from datetime import date, datetime

os.environ.setdefault("FLASK_ENV", "development")

from app import create_app
from app.config import DevelopmentConfig
from app.extensions import db


def _app():
    tmpdb = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmpdb.close()
    _orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmpdb.name}"
    try:
        app = create_app("development")
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = _orig
    with app.app_context():
        db.create_all()
    return app


def _seed_match(*, dated: bool, with_venue: bool):
    from app.models import (
        AgeGroup, Club, Competition, CompetitionTeam, Match, Season, Stage, Team, Venue,
    )
    ag = AgeGroup(name_ar="تحت 17", name_en="U17", oldest_birth_year=2009)
    c1 = Club(name_ar="الأهلي", name_en="Ahly")
    c2 = Club(name_ar="الزمالك", name_en="Zamalek")
    db.session.add_all([ag, c1, c2])
    db.session.flush()
    home = Team(club_id=c1.id, age_group_id=ag.id)
    away = Team(club_id=c2.id, age_group_id=ag.id)
    season = Season(name_ar="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    db.session.add_all([home, away, season])
    db.session.flush()
    comp = Competition(season_id=season.id, age_group_id=ag.id, code="c1",
                       name_ar="الدوري", sector_ar="القاهرة")
    db.session.add(comp)
    db.session.flush()
    stage = Stage(competition_id=comp.id, stage_order=1, type="league")
    db.session.add(stage)
    db.session.flush()
    db.session.add_all([
        CompetitionTeam(competition_id=comp.id, team_id=home.id),
        CompetitionTeam(competition_id=comp.id, team_id=away.id),
    ])
    venue = None
    if with_venue:
        venue = Venue(name_ar="ستاد القاهرة", url="https://maps/x")
        db.session.add(venue)
        db.session.flush()
    m = Match(
        stage_id=stage.id, home_team_id=home.id, away_team_id=away.id, status="scheduled",
        match_date=datetime(2026, 3, 1, 15, 0) if dated else None,
        venue_id=venue.id if venue else None,
    )
    db.session.add(m)
    db.session.commit()
    return m.id, comp.id


def test_dated_match_emits_event_with_venue_location():
    app = _app()
    with app.app_context():
        import app as app_pkg
        mid, _ = _seed_match(dated=True, with_venue=True)
        ev = app_pkg._match_share_meta(mid)["event"]
        assert ev["startDate"] == "2026-03-01T15:00:00"
        assert ev["endDate"] == "2026-03-01T17:00:00"
        assert ev["location"]["name"] == "ستاد القاهرة"
        assert ev["location"]["url"] == "https://maps/x"
        assert ev["eventStatus"] == "https://schema.org/EventScheduled"
        assert {t["name"] for t in ev["performer"]} == {"الأهلي", "الزمالك"}
        assert ev["organizer"]["name"] == "الدوري"


def test_dated_match_falls_back_to_sector_location():
    app = _app()
    with app.app_context():
        import app as app_pkg
        mid, _ = _seed_match(dated=True, with_venue=False)
        ev = app_pkg._match_share_meta(mid)["event"]
        assert ev["location"]["name"] == "القاهرة"  # the competition's sector


def test_tbd_match_emits_no_event():
    app = _app()
    with app.app_context():
        import app as app_pkg
        mid, _ = _seed_match(dated=False, with_venue=True)
        assert app_pkg._match_share_meta(mid)["event"] == {}


def test_competition_event_uses_season_dates():
    app = _app()
    with app.app_context():
        import app as app_pkg
        _, cid = _seed_match(dated=True, with_venue=True)
        ev = app_pkg._competition_share_meta(cid, tab="matches")["event"]
        assert ev["startDate"] == "2026-01-01"
        assert ev["endDate"] == "2026-12-31"
        assert ev["location"]["name"] == "القاهرة"
        assert ev["organizer"]["name"] == "الدوري"
