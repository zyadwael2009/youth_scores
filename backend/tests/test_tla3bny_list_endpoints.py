"""Advanced-audit M6: the awards / punishments list endpoints eager-load their
relations (to kill N+1) and bound the response. This guards that the joins still
resolve the nested names correctly and the public lists return the expected rows."""

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
    ac = Tla3bnyAcademy(name="Falcons", status="approved")
    db.session.add(ac)
    db.session.flush()
    team = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="Falcons U14")
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
    player = Tla3bnyPlayer(name="Star Kid", dob=date(2011, 1, 1))
    db.session.add(player)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionPlayer(
        competition_team_id=entry.id, player_id=player.id, status="approved"))
    admin = Tla3bnyUser(username="s", role="super_admin", status="active", password_hash="x")
    db.session.add(admin)
    db.session.commit()
    return {"comp_id": comp.id, "cage_id": cage.id, "team_id": team.id,
            "player_id": player.id, "token": auth.generate_token(admin)}


def test_award_and_punishment_lists_resolve_eager_loaded_relations(client):
    app, db = client
    c = app.test_client()
    s = _seed(db)
    hdr = {"Authorization": f"Bearer {s['token']}"}

    # Grant a player award and record a (public) point deduction.
    assert c.post(f"/api/tla3bny/competitions/{s['comp_id']}/awards",
                  json={"award_type": "best_player", "player_id": s["player_id"],
                        "competition_age_id": s["cage_id"]}, headers=hdr).status_code == 201
    assert c.post(f"/api/tla3bny/competitions/{s['comp_id']}/punishments",
                  json={"punishment_type": "point_deduction", "team_id": s["team_id"],
                        "points": 3}, headers=hdr).status_code in (200, 201)

    # Public awards list: the joined player name resolves.
    awards = c.get(f"/api/tla3bny/competitions/{s['comp_id']}/awards").get_json()
    best = [a for a in awards if a["award_type"] == "best_player"]
    assert len(best) == 1 and best[0]["player_name"] == "Star Kid"

    # Public punishments list: the joined team name resolves (point deductions are public).
    puns = c.get(f"/api/tla3bny/competitions/{s['comp_id']}/punishments").get_json()
    deductions = [p for p in puns if p["punishment_type"] == "point_deduction"]
    assert len(deductions) == 1 and deductions[0]["team_name"] == "Falcons U14"
