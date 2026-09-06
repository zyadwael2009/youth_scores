"""Advanced-roadmap perf: standings form is built in one pass (_forms_by_team) instead
of re-scanning all matches per team. This pins the output shape (newest-first W/D/L)."""

import os
import tempfile
from datetime import date

import pytest


@pytest.fixture()
def db_ctx():
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


def test_forms_by_team_is_newest_first_wdl(db_ctx):
    db = db_ctx
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyMatch,
        Tla3bnySeason, Tla3bnyTeam,
    )
    from app.services import tla3bny_tables as tables

    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    t = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="T")
    o = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="O")
    db.session.add_all([t, o])
    db.session.flush()
    comp = Tla3bnyCompetition(name="L", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()

    def _m(home, away, hs, aws, d):
        db.session.add(Tla3bnyMatch(
            competition_id=comp.id, age_category_id=age.id, home_team_id=home,
            away_team_id=away, home_score=hs, away_score=aws, status="finished", date=d))

    _m(t.id, o.id, 2, 0, date(2026, 9, 1))   # T win
    _m(t.id, o.id, 1, 1, date(2026, 9, 8))   # draw
    _m(o.id, t.id, 3, 0, date(2026, 9, 15))  # T loss (played latest)
    db.session.commit()

    matches = Tla3bnyMatch.query.filter_by(competition_id=comp.id).all()
    forms = tables._forms_by_team(matches)
    assert forms[t.id] == ["L", "D", "W"]  # newest first
    assert forms[o.id] == ["W", "D", "L"]  # mirror
