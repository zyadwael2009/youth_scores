"""The registration → approval money-path (previously untested end-to-end):
registering a team auto-enqueues its squad up to the per-team cap, an organizer
approves a pending player, the cap blocks an over-limit add, and only an organizer
may register a team.
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
    """A competition running one age with a per-team cap of 2, an academy whose team
    has THREE active squad players (national IDs set), a super-admin organizer, and an
    academy login. Returns the ids + tokens needed to drive the endpoints."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyCompetitionAge,
        Tla3bnyPlayer, Tla3bnyPlayerTeam, Tla3bnySeason, Tla3bnyTeam, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    team = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="T")
    db.session.add(team)
    db.session.flush()
    players = []
    for i in range(3):
        p = Tla3bnyPlayer(name=f"P{i}", dob=date(2011, 1, 1 + i),
                          national_id=f"2901101000000{i}")
        db.session.add(p)
        db.session.flush()
        db.session.add(Tla3bnyPlayerTeam(player_id=p.id, team_id=team.id, status="active"))
        players.append(p.id)
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionAge(
        competition_id=comp.id, age_category_id=age.id, max_players_per_team=2))
    admin = Tla3bnyUser(username="s", role="super_admin", status="active", password_hash="x")
    acad_user = Tla3bnyUser(username="a", role="academy", status="active",
                            password_hash="x", academy_id=ac.id)
    db.session.add_all([admin, acad_user])
    db.session.commit()
    return {
        "comp_id": comp.id, "team_id": team.id, "players": players,
        "admin": auth.generate_token(admin), "academy": auth.generate_token(acad_user),
    }


def _register(c, s, token):
    return c.post(f"/api/tla3bny/competitions/{s['comp_id']}/teams",
                  json={"team_id": s["team_id"]},
                  headers={"Authorization": f"Bearer {token}"})


def _pending(db, comp_id):
    from app.models import Tla3bnyCompetitionPlayer, Tla3bnyCompetitionTeam
    return (Tla3bnyCompetitionPlayer.query
            .join(Tla3bnyCompetitionTeam)
            .filter(Tla3bnyCompetitionTeam.competition_id == comp_id).all())


def test_registering_a_team_auto_enqueues_up_to_the_cap(client):
    app, db = client
    s = _seed(db)
    r = _register(app.test_client(), s, s["admin"])
    assert r.status_code == 201
    rows = _pending(db, s["comp_id"])
    # 3 squad players, cap 2 → only 2 enqueued, all pending.
    assert len(rows) == 2
    assert all(cp.status == "pending" for cp in rows)


def test_organizer_can_approve_a_pending_player(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    _register(c, s, s["admin"])
    cp = _pending(db, s["comp_id"])[0]
    # Approving is gated on the required papers; "force" is the organizer's documented
    # override (papers verified physically / not yet scanned).
    r = c.post(f"/api/tla3bny/competition-players/{cp.id}/approve",
               json={"force": True}, headers={"Authorization": f"Bearer {s['admin']}"})
    assert r.status_code == 200
    db.session.refresh(cp)
    assert cp.status == "approved"


def test_approve_without_required_papers_is_blocked(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    _register(c, s, s["admin"])
    cp = _pending(db, s["comp_id"])[0]
    # No papers uploaded and no force → the required-documents gate blocks it.
    r = c.post(f"/api/tla3bny/competition-players/{cp.id}/approve",
               headers={"Authorization": f"Bearer {s['admin']}"})
    assert r.status_code == 409


def test_add_beyond_the_per_team_cap_is_rejected(client):
    app, db = client
    from app.models import Tla3bnyCompetitionTeam
    c = app.test_client()
    s = _seed(db)
    _register(c, s, s["admin"])  # fills 2 of 2
    entry = Tla3bnyCompetitionTeam.query.filter_by(
        competition_id=s["comp_id"], team_id=s["team_id"]).first()
    # The 3rd squad player isn't on the roster yet; adding them overflows the cap.
    third = s["players"][2]
    r = c.post(f"/api/tla3bny/competition-teams/{entry.id}/players",
               json={"player_id": third},
               headers={"Authorization": f"Bearer {s['admin']}"})
    assert r.status_code == 409


def test_only_an_organizer_may_register_a_team(client):
    app, db = client
    s = _seed(db)
    # The academy login is not a competition admin → forbidden.
    r = _register(app.test_client(), s, s["academy"])
    assert r.status_code == 403
