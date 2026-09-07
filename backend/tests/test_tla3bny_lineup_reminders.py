"""The "submit your lineup" reminder task: pings the staff of a team that hasn't posted
a lineup for a match whose deadline is approaching, once per match."""

import os
import tempfile
from datetime import date, datetime

import pytest


@pytest.fixture()
def app_db():
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
    """A scheduled 16:00 match; the AWAY team has a lineup, the HOME team doesn't."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyLineup,
        Tla3bnyLineupSlot, Tla3bnyMatch, Tla3bnyPlayer, Tla3bnySeason, Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    h = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="Home")
    a = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="Away")
    db.session.add_all([h, a])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    m = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id, home_team_id=h.id,
                     away_team_id=a.id, date=date(2026, 9, 10), time="16:00", status="scheduled")
    p = Tla3bnyPlayer(name="Away Kid")
    db.session.add_all([m, p])
    db.session.flush()
    lu = Tla3bnyLineup(match_id=m.id, team_id=a.id)  # away submitted
    db.session.add(lu)
    db.session.flush()
    db.session.add(Tla3bnyLineupSlot(lineup_id=lu.id, player_id=p.id))
    db.session.commit()
    return {"match": m.id, "home": h.id, "away": a.id}


# 14:00 on match day → inside the window before a 15:00 deadline (16:00 − 60 min).
IN_WINDOW = datetime(2026, 9, 10, 14, 0)


def test_reminds_only_the_team_without_a_lineup(app_db, monkeypatch):
    app, db = app_db
    from app.models import Tla3bnyMatch
    from app.services import notifications as n
    from app.services import tla3bny_reminders as r
    s = _seed(db)

    topics = []
    monkeypatch.setattr(n, "send_to_topic",
                        lambda topic, title, body, data=None: topics.append(topic) or {})
    result = r.send_due_lineup_reminders(now_local=IN_WINDOW)

    assert result == {"matches": 1, "teams": 1}
    assert n.tla3bny_team_topic(s["home"]) in topics       # home has no lineup → reminded
    assert n.tla3bny_team_topic(s["away"]) not in topics   # away already submitted
    assert db.session.get(Tla3bnyMatch, s["match"]).lineup_reminder_sent_at is not None

    # Running again does nothing — the match is flagged.
    topics.clear()
    assert r.send_due_lineup_reminders(now_local=IN_WINDOW) == {"matches": 0, "teams": 0}
    assert topics == []


def test_no_reminder_outside_the_window(app_db, monkeypatch):
    app, db = app_db
    from app.services import notifications as n
    from app.services import tla3bny_reminders as r
    _seed(db)
    monkeypatch.setattr(n, "send_to_topic", lambda *a, **k: {})
    # 09:00 is well before the 12:00–15:00 reminder window.
    assert r.send_due_lineup_reminders(now_local=datetime(2026, 9, 10, 9, 0)) == {"matches": 0, "teams": 0}


def test_task_endpoint_requires_the_admin_key(app_db):
    app, db = app_db
    _seed(db)
    app.config["ADMIN_API_KEY"] = "secret-key"
    c = app.test_client()

    assert c.post("/api/tla3bny/tasks/lineup-reminders").status_code == 403
    ok = c.post("/api/tla3bny/tasks/lineup-reminders", headers={"X-Admin-Key": "secret-key"})
    assert ok.status_code == 200 and ok.get_json()["status"] == "ok"
