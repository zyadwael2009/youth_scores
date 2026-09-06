"""Advanced-audit M2 + M3.

M3 — enter_result validates ET/penalty consistency (ET is cumulative so ≥ FT; a
shootout only breaks a level score and can't end level).
M2 — team-of-round slots must reference players approved in the competition.
"""

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
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition,
        Tla3bnyCompetitionAge, Tla3bnyCompetitionPlayer, Tla3bnyCompetitionTeam,
        Tla3bnyMatch, Tla3bnyPlayer, Tla3bnySeason, Tla3bnyTeam, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    a = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="A")
    b = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="B")
    db.session.add_all([a, b])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionAge(competition_id=comp.id, age_category_id=age.id))
    ea = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=a.id, age_category_id=age.id)
    eb = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=b.id, age_category_id=age.id)
    db.session.add_all([ea, eb])
    db.session.flush()
    match = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id,
                         home_team_id=a.id, away_team_id=b.id, status="scheduled")
    # An approved player (eligible for team-of-round) and an unapproved one.
    approved = Tla3bnyPlayer(name="Approved", dob=date(2011, 3, 1))
    unapproved = Tla3bnyPlayer(name="Unapproved", dob=date(2011, 4, 1))
    db.session.add_all([match, approved, unapproved])
    db.session.flush()
    db.session.add(Tla3bnyCompetitionPlayer(
        competition_team_id=ea.id, player_id=approved.id, status="approved"))
    admin = Tla3bnyUser(username="s", role="super_admin", status="active", password_hash="x")
    db.session.add(admin)
    db.session.commit()
    return {
        "comp_id": comp.id, "match_id": match.id, "token": auth.generate_token(admin),
        "approved_pid": approved.id, "unapproved_pid": unapproved.id,
    }


def _result(c, s, body):
    return c.post(f"/api/tla3bny/matches/{s['match_id']}/result",
                  json=body, headers={"Authorization": f"Bearer {s['token']}"})


def test_extra_time_below_full_time_is_rejected(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    # ET is cumulative from kick-off, so 0-0 after a 1-1 at 90' is impossible.
    r = _result(c, s, {"home_score": 1, "away_score": 1,
                       "home_score_et": 0, "away_score_et": 0})
    assert r.status_code == 400


def test_tied_shootout_is_rejected(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    r = _result(c, s, {"home_score": 1, "away_score": 1,
                       "home_score_pen": 3, "away_score_pen": 3})
    assert r.status_code == 400


def test_shootout_on_a_non_level_score_is_rejected(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    r = _result(c, s, {"home_score": 2, "away_score": 1,
                       "home_score_pen": 4, "away_score_pen": 3})
    assert r.status_code == 400


def test_consistent_extra_time_and_penalties_are_accepted(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    r = _result(c, s, {"home_score": 1, "away_score": 1,
                       "home_score_et": 2, "away_score_et": 2,
                       "home_score_pen": 4, "away_score_pen": 3})
    assert r.status_code == 200
    # A plain FT score with no ET/pens is fine too.
    assert _result(c, s, {"home_score": 3, "away_score": 0}).status_code == 200


def _totr(c, s, slots):
    return c.put(f"/api/tla3bny/competitions/{s['comp_id']}/team-of-round",
                 json={"round": "R1", "slots": slots},
                 headers={"Authorization": f"Bearer {s['token']}"})


def test_team_of_round_rejects_unapproved_player(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    r = _totr(c, s, [{"player_id": s["unapproved_pid"], "position_slot": "GK"}])
    assert r.status_code == 409


def test_team_of_round_accepts_approved_player(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    r = _totr(c, s, [{"player_id": s["approved_pid"], "position_slot": "GK"}])
    assert r.status_code == 200
