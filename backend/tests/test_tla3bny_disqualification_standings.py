"""Advanced-audit H2: a disqualified team is dropped from the standings table, but its
matches still count for its opponents (who keep the result). Driven by the
disqualification punishment, so it's reversible if the organizer lifts it."""

import os
import tempfile

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


def _seed(db):
    """Three teams A, B, C. B beat A; C beat B. B will be disqualified."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition,
        Tla3bnyCompetitionAge, Tla3bnyCompetitionTeam, Tla3bnyMatch,
        Tla3bnySeason, Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    teams = {}
    for key in ("A", "B", "C"):
        t = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name=key)
        db.session.add(t)
        db.session.flush()
        teams[key] = t.id
    comp = Tla3bnyCompetition(name="League", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionAge(competition_id=comp.id, age_category_id=age.id))
    for tid in teams.values():
        db.session.add(Tla3bnyCompetitionTeam(
            competition_id=comp.id, team_id=tid, age_category_id=age.id))

    def _m(home, away, hs, aws):
        db.session.add(Tla3bnyMatch(
            competition_id=comp.id, age_category_id=age.id,
            home_team_id=teams[home], away_team_id=teams[away],
            home_score=hs, away_score=aws, status="finished"))

    _m("B", "A", 2, 0)  # B beat A
    _m("C", "B", 1, 0)  # C beat B
    db.session.commit()
    return comp.id, age.id, teams


def _flatten(tables):
    return {r["team_id"]: r for grp in tables for r in grp["standings"]}


def test_disqualified_team_dropped_but_opponents_keep_results(db_ctx):
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.services import tla3bny_tables as tables

    comp_id, age_id, teams = _seed(db)

    # Baseline: all three teams present, B has 3 pts from beating A.
    before = _flatten(tables.standings_by_group(comp_id, age_id))
    assert set(before) == {teams["A"], teams["B"], teams["C"]}
    assert before[teams["B"]]["Pts"] == 3

    # Disqualify B.
    db.session.add(Tla3bnyPunishment(
        competition_id=comp_id, team_id=teams["B"], punishment_type="disqualification"))
    db.session.commit()

    after = _flatten(tables.standings_by_group(comp_id, age_id))
    # B is gone from the table…
    assert teams["B"] not in after
    assert set(after) == {teams["A"], teams["C"]}
    # …but A keeps its loss to B and C keeps its win over B.
    assert after[teams["A"]]["P"] == 1 and after[teams["A"]]["L"] == 1 and after[teams["A"]]["Pts"] == 0
    assert after[teams["C"]]["P"] == 1 and after[teams["C"]]["W"] == 1 and after[teams["C"]]["Pts"] == 3


def test_lifting_the_disqualification_restores_the_team(db_ctx):
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.services import tla3bny_tables as tables

    comp_id, age_id, teams = _seed(db)
    pun = Tla3bnyPunishment(
        competition_id=comp_id, team_id=teams["B"], punishment_type="disqualification")
    db.session.add(pun)
    db.session.commit()
    assert teams["B"] not in _flatten(tables.standings_by_group(comp_id, age_id))

    db.session.delete(pun)
    db.session.commit()
    assert teams["B"] in _flatten(tables.standings_by_group(comp_id, age_id))
