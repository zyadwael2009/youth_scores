"""Match-ban auto-expiry: how many matches a banned player has "served".

The count is anchored to the match the ban starts after (``Tla3bnyPunishment.match_id``)
and served by the banned player's OWN team's fixtures — not the lineup being
checked. This fixes the earlier date-based heuristic, which mixed a UTC ban
timestamp with local match dates and couldn't order same-day / undated matches or
stop a player dodging the ban by guesting for another team.
"""

import os
import tempfile
from datetime import date, timedelta

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
    """A competition with one academy holding two teams (A, B)."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition,
        Tla3bnyCompetitionTeam, Tla3bnySeason, Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2012", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="A", status="approved")
    db.session.add(ac)
    db.session.flush()
    team_a = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="A")
    team_b = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="B")
    team_c = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="C")
    db.session.add_all([team_a, team_b, team_c])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    entry_a = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=team_a.id, age_category_id=age.id)
    entry_b = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=team_b.id, age_category_id=age.id)
    entry_c = Tla3bnyCompetitionTeam(competition_id=comp.id, team_id=team_c.id, age_category_id=age.id)
    db.session.add_all([entry_a, entry_b, entry_c])
    db.session.flush()
    return {
        "comp_id": comp.id, "age_id": age.id,
        "team_a": team_a.id, "team_b": team_b.id, "team_c": team_c.id,
        "entry_a": entry_a.id, "entry_b": entry_b.id, "entry_c": entry_c.id,
    }


def _approve_player(db, entry_id, name):
    from app.models import Tla3bnyCompetitionPlayer, Tla3bnyPlayer
    p = Tla3bnyPlayer(name=name)
    db.session.add(p)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionPlayer(
        competition_team_id=entry_id, player_id=p.id, status="approved"))
    db.session.flush()
    return p.id


def _match(db, s, home, away, status="finished", d=None):
    from app.models import Tla3bnyMatch
    m = Tla3bnyMatch(competition_id=s["comp_id"], age_category_id=s["age_id"],
                     home_team_id=home, away_team_id=away, status=status, date=d)
    db.session.add(m)
    db.session.flush()
    return m


def test_served_count_advances_with_the_teams_matches(db_ctx):
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons
    from app.api.tla3bny.punishments import _ban_anchor_match_id

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    d0 = date(2026, 9, 1)
    offense = _match(db, s, s["team_a"], s["team_b"], "finished", d0)
    db.session.commit()

    # The ban anchors to the team's latest finished match (the offense match).
    anchor_id = _ban_anchor_match_id(s["comp_id"], pid, None)
    assert anchor_id == offense.id
    ban = Tla3bnyPunishment(competition_id=s["comp_id"], player_id=pid,
                            punishment_type="match_ban", matches=2, match_id=anchor_id)
    db.session.add(ban)
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", d0 + timedelta(days=21))

    # 0 of 2 served (only the offense match is finished, and it doesn't count).
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])

    # One more finished match → 1 of 2 served, still blocked.
    _match(db, s, s["team_a"], s["team_b"], "finished", d0 + timedelta(days=7))
    db.session.commit()
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])

    # Second finished match → 2 of 2 served, ban lifts automatically.
    _match(db, s, s["team_a"], s["team_b"], "finished", d0 + timedelta(days=14))
    db.session.commit()
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])


def test_same_day_and_undated_matches_count(db_ctx):
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    d0 = date(2026, 9, 1)
    offense = _match(db, s, s["team_a"], s["team_b"], "finished", d0)
    db.session.commit()

    ban = Tla3bnyPunishment(competition_id=s["comp_id"], player_id=pid,
                            punishment_type="match_ban", matches=2, match_id=offense.id)
    db.session.add(ban)
    # A finished match on the SAME day as the offense (later id) must count as served…
    _match(db, s, s["team_a"], s["team_b"], "finished", d0)
    # …and so must a finished match with no date recorded (the old code dropped it).
    _match(db, s, s["team_a"], s["team_b"], "finished", None)
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", d0 + timedelta(days=30))
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])  # 2 of 2 served


def test_ban_is_served_by_own_team_not_the_guesting_team(db_ctx):
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")  # approved on team A
    d0 = date(2026, 9, 1)
    offense = _match(db, s, s["team_a"], s["team_b"], "finished", d0)
    db.session.commit()

    ban = Tla3bnyPunishment(competition_id=s["comp_id"], player_id=pid,
                            punishment_type="match_ban", matches=1, match_id=offense.id)
    db.session.add(ban)
    # Team B plays several matches (against team C, so team A isn't involved) — these
    # must NOT serve a ban earned at team A, or the player could dodge it by guesting.
    _match(db, s, s["team_b"], s["team_c"], "finished", d0 + timedelta(days=3))
    _match(db, s, s["team_b"], s["team_c"], "finished", d0 + timedelta(days=6))
    db.session.commit()

    # Checking team B's lineup: the player is still blocked (own team A hasn't played
    # since the ban), even though team B has finished two matches.
    b_upcoming = _match(db, s, s["team_b"], s["team_c"], "scheduled", d0 + timedelta(days=30))
    assert pid in _blocked_player_reasons(b_upcoming, s["team_b"])

    # Team A finally plays one → 1 of 1 served → no longer blocked anywhere.
    _match(db, s, s["team_a"], s["team_c"], "finished", d0 + timedelta(days=10))
    db.session.commit()
    assert pid not in _blocked_player_reasons(b_upcoming, s["team_b"])


def test_legacy_ban_without_anchor_falls_back_to_recording_time(db_ctx):
    db = db_ctx
    from datetime import datetime
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    # A pre-existing ban with no anchor match (match_id NULL).
    ban = Tla3bnyPunishment(competition_id=s["comp_id"], player_id=pid,
                            punishment_type="match_ban", matches=1)
    db.session.add(ban)
    db.session.flush()
    ban.created_at = datetime(2026, 9, 5, 12, 0, 0)
    # A match BEFORE the ban must not count; a match AFTER it must.
    _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 1))
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", date(2026, 10, 1))
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # nothing served yet

    _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 12))
    db.session.commit()
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])  # 1 of 1 served
