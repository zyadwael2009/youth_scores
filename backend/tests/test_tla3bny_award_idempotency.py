"""Advanced-audit M5: granting a singular award is idempotent — re-granting replaces
the holder rather than piling up duplicate rows. (The FOR UPDATE lock that makes this
safe under concurrent double-submits is a no-op on SQLite, so this verifies the
single-threaded replace-then-insert; the lock mirrors the caps/deduction pattern.)"""

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
        Tla3bnyPlayer, Tla3bnySeason, Tla3bnyTeam, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    team = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="A")
    db.session.add(team)
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    cage = Tla3bnyCompetitionAge(competition_id=comp.id, age_category_id=age.id)
    db.session.add(cage)
    db.session.flush()
    entry = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=team.id, age_category_id=age.id)
    db.session.add(entry)
    db.session.flush()
    player = Tla3bnyPlayer(name="Star", dob=date(2011, 2, 2))
    db.session.add(player)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionPlayer(
        competition_team_id=entry.id, player_id=player.id, status="approved"))
    admin = Tla3bnyUser(username="s", role="super_admin", status="active", password_hash="x")
    db.session.add(admin)
    db.session.commit()
    return {
        "comp_id": comp.id, "cage_id": cage.id, "team_id": team.id,
        "player_id": player.id, "token": auth.generate_token(admin),
    }


def _grant(c, s, body):
    return c.post(f"/api/tla3bny/competitions/{s['comp_id']}/awards",
                  json=body, headers={"Authorization": f"Bearer {s['token']}"})


def test_regranting_a_title_replaces_rather_than_duplicates(client):
    app, db = client
    from app.models import Tla3bnyAward
    c = app.test_client()
    s = _seed(db)

    body = {"award_type": "champion", "team_id": s["team_id"], "competition_age_id": s["cage_id"]}
    assert _grant(c, s, body).status_code == 201
    assert _grant(c, s, body).status_code == 201  # re-grant

    champions = Tla3bnyAward.query.filter_by(
        competition_id=s["comp_id"], award_type="champion").all()
    assert len(champions) == 1  # single holder, not two


def test_regranting_a_player_award_replaces(client):
    app, db = client
    from app.models import Tla3bnyAward
    c = app.test_client()
    s = _seed(db)

    body = {"award_type": "best_player", "player_id": s["player_id"], "competition_age_id": s["cage_id"]}
    assert _grant(c, s, body).status_code == 201
    assert _grant(c, s, body).status_code == 201

    awards = Tla3bnyAward.query.filter_by(
        competition_id=s["comp_id"], award_type="best_player").all()
    assert len(awards) == 1
