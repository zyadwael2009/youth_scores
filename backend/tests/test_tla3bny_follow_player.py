"""Player following: a parent follows their child's player topic and is pinged when
the child scores."""

import os
import tempfile

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


def _match(db):
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyMatch,
        Tla3bnySeason, Tla3bnyTeam,
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
                     away_team_id=a.id, home_score=2, away_score=1, status="finished")
    db.session.add(m)
    db.session.commit()
    return m


def test_player_follow_topic_is_namespaced():
    from app.services import notifications as n
    assert n.tla3bny_player_follow_topic(9) == "t3_playerfollow_9"
    assert n.tla3bny_player_follow_topic(9) != n.tla3bny_team_follow_topic(9)


def test_goal_pings_each_scorers_follow_topic(app_db, monkeypatch):
    app, db = app_db
    from app.services import notifications as n
    m = _match(db)

    sent = []
    monkeypatch.setattr(n, "send_to_topic",
                        lambda topic, title, body, data=None: sent.append((topic, title)) or {})
    n.notify_tla3bny_player_goals(m, {42: "Kid A", 43: "Kid B"})

    topics = {t for t, _title in sent}
    assert n.tla3bny_player_follow_topic(42) in topics
    assert n.tla3bny_player_follow_topic(43) in topics
    # The title names the scorer.
    assert any("Kid A" in title for _t, title in sent)


def test_follow_player_endpoint_validates_and_subscribes(app_db, monkeypatch):
    app, _db = app_db
    from app.services import notifications as n
    monkeypatch.setattr(n, "subscribe_token_to_topic", lambda token, topic: {"topic": topic})
    c = app.test_client()
    tok = "p" * 150

    ok = c.post("/api/tla3bny/push/follow-player", json={"token": tok, "player_id": 5})
    assert ok.status_code == 200 and ok.get_json()["followed_player"] == 5
    assert c.post("/api/tla3bny/push/follow-player", json={"token": tok}).status_code == 400
