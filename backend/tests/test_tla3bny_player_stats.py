"""GET /players/<id>/stats — the per-competition breakdown the player page renders.

Verifies goals/assists/appearances are attributed to the right competition + season,
and that `totals` sums the rows. (The page discarded `by_competition` before; it now
renders it, so this locks the contract.)
"""

import os
import tempfile

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
            yield app.test_client(), db
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
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyLineup,
        Tla3bnyLineupSlot, Tla3bnyMatch, Tla3bnyMatchEvent, Tla3bnyPlayer,
        Tla3bnySeason, Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    s1 = Tla3bnySeason(name="2025-2026")
    s2 = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, s1, s2])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    h = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="H")
    a = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="A")
    db.session.add_all([h, a])
    db.session.flush()
    c1 = Tla3bnyCompetition(name="League A", season_id=s1.id, status="active")
    c2 = Tla3bnyCompetition(name="Cup B", season_id=s2.id, status="active")
    db.session.add_all([c1, c2])
    db.session.flush()
    p = Tla3bnyPlayer(name="Star")
    db.session.add(p)
    db.session.flush()

    def _played(comp, event_type):
        m = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id,
                         home_team_id=h.id, away_team_id=a.id, status="finished")
        db.session.add(m)
        db.session.flush()
        db.session.add(Tla3bnyMatchEvent(match_id=m.id, player_id=p.id, team_id=h.id,
                                         event_type=event_type, is_own_goal=False))
        lu = Tla3bnyLineup(match_id=m.id, team_id=h.id)
        db.session.add(lu)
        db.session.flush()
        db.session.add(Tla3bnyLineupSlot(lineup_id=lu.id, player_id=p.id))

    _played(c1, "goal")     # a goal + appearance in League A (season 2025-2026)
    _played(c2, "assist")   # an assist + appearance in Cup B (season 2026-2027)
    db.session.commit()
    return p.id


def test_player_stats_breaks_down_by_competition_and_season(client):
    c, db = client
    pid = _seed(db)
    r = c.get(f"/api/tla3bny/players/{pid}/stats").get_json()

    by = {row["competition_name"]: row for row in r["by_competition"]}
    assert set(by) == {"League A", "Cup B"}
    assert by["League A"]["goals"] == 1
    assert by["League A"]["appearances"] == 1
    assert by["League A"]["season_name"] == "2025-2026"
    assert by["Cup B"]["assists"] == 1
    assert by["Cup B"]["appearances"] == 1
    assert by["Cup B"]["season_name"] == "2026-2027"

    # Career totals sum the per-competition rows.
    assert r["totals"]["goals"] == 1
    assert r["totals"]["assists"] == 1
    assert r["totals"]["appearances"] == 2
