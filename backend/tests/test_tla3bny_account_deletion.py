"""Self-service academy account closure (DELETE /academies/me).

A club that never played is hard-deleted; one with match history is soft-closed
(suspended + PII scrubbed) so its matches and everyone else's standings survive;
and a club still in an unfinished competition can't leave mid-way.
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


def _seed_academy(db):
    """An approved academy with one team, a manager, and an academy-owner login."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAcademyManager, Tla3bnyAgeCategory, Tla3bnyTeam,
        Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2012", sort_order=0)
    db.session.add(age)
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved", phone="0100", logo_path="x.png")
    db.session.add(ac)
    db.session.flush()
    db.session.add(Tla3bnyAcademyManager(academy_id=ac.id, name="Mgr", phone="0111"))
    team = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="T")
    db.session.add(team)
    db.session.flush()
    user = Tla3bnyUser(username="a", role="academy", status="active",
                       password_hash="x", academy_id=ac.id)
    db.session.add(user)
    db.session.commit()
    return {"academy_id": ac.id, "team_id": team.id, "age_id": age.id,
            "token": auth.generate_token(user)}


def _enter(db, s, comp_status, entry_status="active"):
    """Give the team an entry in a competition of the given status."""
    from app.models import Tla3bnyCompetition, Tla3bnyCompetitionTeam, Tla3bnySeason
    season = Tla3bnySeason(name="2026-2027")
    db.session.add(season)
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status=comp_status)
    db.session.add(comp)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionTeam(
        competition_id=comp.id, team_id=s["team_id"], age_category_id=s["age_id"],
        status=entry_status))
    db.session.commit()
    return comp.id


def _play_match(db, s, comp_id):
    """A finished match the team took part in (against a throwaway opponent)."""
    from app.models import Tla3bnyMatch, Tla3bnyTeam
    opp = Tla3bnyTeam(academy_id=s["academy_id"], age_category_id=s["age_id"], name="Opp")
    db.session.add(opp)
    db.session.flush()
    db.session.add(Tla3bnyMatch(
        competition_id=comp_id, age_category_id=s["age_id"],
        home_team_id=s["team_id"], away_team_id=opp.id, status="finished",
        date=date(2026, 1, 1)))
    db.session.commit()


def _delete_me(c, token, **body):
    return c.delete("/api/tla3bny/academies/me", json=body,
                    headers={"Authorization": f"Bearer {token}"})


def test_confirmation_is_required(client):
    app, db = client
    s = _seed_academy(db)
    assert _delete_me(app.test_client(), s["token"]).status_code == 400


def test_never_played_academy_is_hard_deleted(client):
    from app.models import Tla3bnyAcademy
    app, db = client
    s = _seed_academy(db)

    r = _delete_me(app.test_client(), s["token"], confirm=True)
    assert r.status_code == 200
    assert r.get_json()["message"] == "deleted"
    assert Tla3bnyAcademy.query.get(s["academy_id"]) is None


def test_academy_with_match_history_is_soft_closed(client):
    from app.models import Tla3bnyAcademy, Tla3bnyMatch, Tla3bnyTeam, Tla3bnyUser
    app, db = client
    s = _seed_academy(db)
    comp_id = _enter(db, s, comp_status="finished")   # finished → not blocked
    _play_match(db, s, comp_id)

    r = _delete_me(app.test_client(), s["token"], confirm=True)
    assert r.status_code == 200
    assert r.get_json()["message"] == "closed"

    ac = Tla3bnyAcademy.query.get(s["academy_id"])
    assert ac is not None and ac.status == "suspended"
    # Contact PII scrubbed, managers removed…
    assert ac.phone is None and ac.logo_path is None and ac.managers == []
    # …but the team and its match survive, and the login is disabled.
    assert Tla3bnyTeam.query.get(s["team_id"]) is not None
    assert Tla3bnyMatch.query.filter_by(home_team_id=s["team_id"]).first() is not None
    assert Tla3bnyUser.query.filter_by(academy_id=s["academy_id"]).first().status == "suspended"


def test_unfinished_competition_blocks_closure(client):
    from app.models import Tla3bnyAcademy
    app, db = client
    s = _seed_academy(db)
    _enter(db, s, comp_status="active")   # active competition → still competing

    r = _delete_me(app.test_client(), s["token"], confirm=True)
    assert r.status_code == 409
    ac = Tla3bnyAcademy.query.get(s["academy_id"])
    assert ac is not None and ac.status == "approved"
