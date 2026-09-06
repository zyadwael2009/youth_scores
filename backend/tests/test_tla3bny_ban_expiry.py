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


def _match(db, s, home, away, status="finished", d=None, finished_at=None):
    """Create a fixture. Mirrors production: a finished match carries a `finished_at`
    (the immutable finish time the ban logic orders by). Derived from the date at noon
    when not given explicitly; an undated finished match needs an explicit value."""
    from datetime import datetime, time as _time
    from app.models import Tla3bnyMatch
    if finished_at is None and status in ("finished", "completed") and d is not None:
        finished_at = datetime.combine(d, _time(12, 0))
    m = Tla3bnyMatch(competition_id=s["comp_id"], age_category_id=s["age_id"],
                     home_team_id=home, away_team_id=away, status=status, date=d,
                     finished_at=finished_at)
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
    from datetime import datetime
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
    # A finished match on the SAME day as the offense (later finish time) must count…
    _match(db, s, s["team_a"], s["team_b"], "finished", d0)
    # …and so must a finished match with no DATE recorded — it still has a finish time,
    # so it orders after the anchor (the old date key dropped undated matches).
    _match(db, s, s["team_a"], s["team_b"], "finished", None,
           finished_at=datetime(2026, 9, 2, 12, 0))
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


def test_anchorless_ban_serves_from_the_first_match(db_ctx):
    """A no-anchor ban (issued before the team had played, or a legacy row) serves from
    the team's first match onward — it counts all the team's finished matches."""
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons
    from app.api.tla3bny.punishments import _ban_anchor_match_id

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    # Ban issued before the team has played anything → no anchor.
    assert _ban_anchor_match_id(s["comp_id"], pid, None) is None
    db.session.add(Tla3bnyPunishment(
        competition_id=s["comp_id"], player_id=pid, punishment_type="match_ban", matches=2))
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", date(2026, 10, 1))
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # 0 of 2

    _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 1))
    db.session.commit()
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # 1 of 2

    _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 8))
    db.session.commit()
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])  # 2 of 2 served


def test_anchorless_ban_ignores_updated_at_bumps(db_ctx):
    """Regression: the live stopwatch (and score edits, rescheduling) bump a match's
    updated_at. An anchorless ban's served count must depend only on how many matches
    the team has finished — never on a timestamp a later write can move."""
    db = db_ctx
    from datetime import datetime
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    db.session.add(Tla3bnyPunishment(
        competition_id=s["comp_id"], player_id=pid, punishment_type="match_ban", matches=2))
    m1 = _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 1))
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", date(2026, 10, 1))
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # 1 of 2 served

    # Simulate an organizer toggling the stopwatch on that finished match much later:
    # updated_at jumps far into the future. The count must not move.
    m1.updated_at = datetime(2999, 1, 1, 0, 0, 0)
    db.session.commit()
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # still 1 of 2, blocked

    _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 8))
    db.session.commit()
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])  # 2 of 2 served


def test_doubly_rostered_player_resolves_to_one_team_deterministically(db_ctx):
    """A player approved on two teams in the same competition must resolve to the SAME
    team (lowest entry id) at ban-creation and at check time, so the anchor sits in the
    counted fixtures. Serving then follows that team, not the other."""
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import (
        _blocked_player_reasons, _player_competition_team_id)
    from app.api.tla3bny.punishments import _ban_anchor_match_id

    s = _seed(db)
    # Same player on both team A and team B rosters (entry_a < entry_b).
    from app.models import Tla3bnyCompetitionPlayer, Tla3bnyPlayer
    p = Tla3bnyPlayer(name="Both")
    db.session.add(p)
    db.session.flush()
    db.session.add_all([
        Tla3bnyCompetitionPlayer(competition_team_id=s["entry_a"], player_id=p.id, status="approved"),
        Tla3bnyCompetitionPlayer(competition_team_id=s["entry_b"], player_id=p.id, status="approved"),
    ])
    offense = _match(db, s, s["team_a"], s["team_c"], "finished", date(2026, 9, 1))
    db.session.commit()

    # Resolves to team A (lowest entry id), and the anchor is one of A's fixtures.
    assert _player_competition_team_id(s["comp_id"], p.id) == s["team_a"]
    anchor_id = _ban_anchor_match_id(s["comp_id"], p.id, None)
    assert anchor_id == offense.id
    db.session.add(Tla3bnyPunishment(
        competition_id=s["comp_id"], player_id=p.id,
        punishment_type="match_ban", matches=1, match_id=anchor_id))
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_c"], "scheduled", date(2026, 10, 1))
    assert p.id in _blocked_player_reasons(upcoming, s["team_a"])  # A hasn't played since
    # Team B playing does NOT serve the ban (it's counted against team A).
    _match(db, s, s["team_b"], s["team_c"], "finished", date(2026, 9, 5))
    db.session.commit()
    assert p.id in _blocked_player_reasons(upcoming, s["team_a"])
    # Team A playing serves it.
    _match(db, s, s["team_a"], s["team_c"], "finished", date(2026, 9, 9))
    db.session.commit()
    assert p.id not in _blocked_player_reasons(upcoming, s["team_a"])


def test_undated_anchor_still_expires_against_later_dated_matches(db_ctx):
    """Regression: a ban anchored to an UNDATED offense match must still count later
    DATED matches as served. The old order key bucketed undated matches last, so a
    dated match sorted *before* an undated anchor and never counted — a permanent ban."""
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons
    from app.api.tla3bny.punishments import _ban_anchor_match_id

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    offense = _match(db, s, s["team_a"], s["team_b"], "finished", None)  # no date recorded
    db.session.commit()

    anchor_id = _ban_anchor_match_id(s["comp_id"], pid, None)
    assert anchor_id == offense.id
    db.session.add(Tla3bnyPunishment(
        competition_id=s["comp_id"], player_id=pid,
        punishment_type="match_ban", matches=1, match_id=anchor_id))
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", date(2026, 10, 1))
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # 0 of 1 served

    # A later DATED match must serve the ban (the previously-buggy case).
    _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 20))
    db.session.commit()
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])  # 1 of 1 served


def test_disqualification_overrides_a_served_ban(db_ctx):
    """A player whose ban is fully served is normally free — but a disqualification on
    top keeps them blocked (permanent until removed)."""
    db = db_ctx
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    offense = _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 1))
    db.session.commit()
    db.session.add(Tla3bnyPunishment(
        competition_id=s["comp_id"], player_id=pid,
        punishment_type="match_ban", matches=1, match_id=offense.id))
    _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 8))  # serves the ban
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", date(2026, 10, 1))
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])  # ban served → free

    db.session.add(Tla3bnyPunishment(
        competition_id=s["comp_id"], player_id=pid, punishment_type="disqualification"))
    db.session.commit()
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # disqualified → blocked


def test_deleted_anchor_match_degrades_to_the_no_anchor_fallback(db_ctx):
    """If the anchor match is deleted (match_id → NULL via ON DELETE SET NULL), the ban
    keeps enforcing via the no-anchor fallback rather than silently vanishing."""
    db = db_ctx
    from app.models import Tla3bnyMatch, Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    offense = _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 1))
    db.session.commit()
    ban = Tla3bnyPunishment(competition_id=s["comp_id"], player_id=pid,
                            punishment_type="match_ban", matches=1, match_id=offense.id)
    db.session.add(ban)
    db.session.commit()

    # Delete the anchor; SQLite here mirrors the FK's SET NULL by clearing it manually.
    db.session.delete(db.session.get(Tla3bnyMatch, offense.id))
    ban.match_id = None
    db.session.commit()

    # No finished matches remain → fallback counts 0 served → still blocked.
    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", date(2026, 10, 1))
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # still enforced (fallback)


def test_finished_at_is_stamped_once_and_frozen(db_ctx):
    """_stamp_finished records the finish time the first time a match is finished and
    never moves it — so a later result correction or a stopwatch toggle can't shift the
    ban ordering."""
    db = db_ctx
    from datetime import datetime
    from app.api.tla3bny.matches import _stamp_finished

    s = _seed(db)
    m = _match(db, s, s["team_a"], s["team_b"], "scheduled", None)
    assert m.finished_at is None  # scheduled → not stamped

    m.status = "finished"
    _stamp_finished(m)
    first = m.finished_at
    assert first is not None

    # A later re-finish / correction / timer write must not overwrite it.
    m.updated_at = datetime(2999, 1, 1)
    _stamp_finished(m)
    assert m.finished_at == first


def test_ban_ordering_follows_finish_time_for_undated_matches(db_ctx):
    """With finish time driving the order, an undated match that finished AFTER the
    anchor counts even though it has no date and a lower id than a later fixture."""
    db = db_ctx
    from datetime import datetime
    from app.models import Tla3bnyPunishment
    from app.api.tla3bny.matches import _blocked_player_reasons

    s = _seed(db)
    pid = _approve_player(db, s["entry_a"], "Banned")
    offense = _match(db, s, s["team_a"], s["team_b"], "finished", date(2026, 9, 1))
    db.session.commit()
    db.session.add(Tla3bnyPunishment(
        competition_id=s["comp_id"], player_id=pid,
        punishment_type="match_ban", matches=1, match_id=offense.id))
    db.session.commit()

    upcoming = _match(db, s, s["team_a"], s["team_b"], "scheduled", date(2026, 10, 1))
    assert pid in _blocked_player_reasons(upcoming, s["team_a"])  # 0 served

    # An UNDATED match that finished after the offense serves the ban (ordered by its
    # finish time, not date/id).
    _match(db, s, s["team_a"], s["team_b"], "finished", None,
           finished_at=datetime(2026, 9, 5, 12, 0))
    db.session.commit()
    assert pid not in _blocked_player_reasons(upcoming, s["team_a"])  # 1 of 1 served
