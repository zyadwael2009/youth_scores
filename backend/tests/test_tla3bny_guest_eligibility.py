"""Advanced-audit H1: a guest player must be an APPROVED competition player on their
own team's entry in this competition. Guesting is cross-age *within* the competition —
not a way to field a player who was never registered/approved (which would dodge the
papers, national-ID clash check, and roster/priced caps)."""

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


def _seed(db, approve_guest: bool):
    """An academy with a primary (older) team entered in a competition and a younger
    sibling team also entered. A player sits on the sibling team. `approve_guest`
    controls whether that player is an approved competition player on the sibling's
    entry. Returns (match, primary_team_id, guest_player_id)."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition,
        Tla3bnyCompetitionPlayer, Tla3bnyCompetitionTeam, Tla3bnyMatch,
        Tla3bnyPlayer, Tla3bnyPlayerTeam, Tla3bnySeason, Tla3bnyTeam,
    )
    old = Tla3bnyAgeCategory(label="2010", sort_order=0)   # oldest_birth_year 2010
    young = Tla3bnyAgeCategory(label="2012", sort_order=1)  # younger
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([old, young, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="A", status="approved")
    db.session.add(ac)
    db.session.flush()
    primary = Tla3bnyTeam(academy_id=ac.id, age_category_id=old.id, name="U16")
    sibling = Tla3bnyTeam(academy_id=ac.id, age_category_id=young.id, name="U14")
    db.session.add_all([primary, sibling])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    e_primary = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=primary.id, age_category_id=old.id)
    e_sibling = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=sibling.id, age_category_id=young.id)
    db.session.add_all([e_primary, e_sibling])
    db.session.flush()
    # A younger player on the sibling team (year 2012 >= 2010 → passes the age gate).
    p = Tla3bnyPlayer(name="Young Guest", dob=date(2012, 5, 1), national_id="29012011234567")
    db.session.add(p)
    db.session.flush()
    db.session.add(Tla3bnyPlayerTeam(player_id=p.id, team_id=sibling.id, status="active"))
    if approve_guest:
        db.session.add(Tla3bnyCompetitionPlayer(
            competition_team_id=e_sibling.id, player_id=p.id, status="approved"))
    match = Tla3bnyMatch(competition_id=comp.id, age_category_id=old.id,
                         home_team_id=primary.id, away_team_id=primary.id, status="scheduled")
    db.session.add(match)
    db.session.commit()
    return match, primary.id, p.id


def test_unapproved_guest_is_excluded(db_ctx):
    db = db_ctx
    from app.api.tla3bny.matches import _lineup_eligible_players
    match, primary_id, guest_id = _seed(db, approve_guest=False)
    eligible_ids = {e["player_id"] for e in _lineup_eligible_players(match, primary_id)}
    assert guest_id not in eligible_ids  # never registered/approved → not a guest option


def test_approved_guest_is_included(db_ctx):
    db = db_ctx
    from app.api.tla3bny.matches import _lineup_eligible_players
    match, primary_id, guest_id = _seed(db, approve_guest=True)
    eligible = _lineup_eligible_players(match, primary_id)
    guest = next((e for e in eligible if e["player_id"] == guest_id), None)
    assert guest is not None and guest["guest"] is True  # approved sibling → eligible guest
