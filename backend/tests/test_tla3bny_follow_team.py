"""Team following: a fan follows one team's results topic (distinct from the private
team chat topic), and a match result fans out to both teams' follow topics."""

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


def test_team_follow_topic_is_distinct_from_the_chat_topic():
    from app.services import notifications as n
    assert n.tla3bny_team_follow_topic(7) == "t3_teamfollow_7"
    # Must NOT be the private chat topic, or a fan would receive the team's chat.
    assert n.tla3bny_team_follow_topic(7) != n.tla3bny_team_topic(7)


def test_match_result_notifies_both_teams_follow_topics(app_db, monkeypatch):
    app, db = app_db
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyMatch,
        Tla3bnySeason, Tla3bnyTeam,
    )
    from app.services import notifications as n

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

    topics = []
    monkeypatch.setattr(n, "send_to_topic",
                        lambda topic, title, body, data=None: topics.append(topic) or {})
    n.notify_tla3bny_match_result(m)

    assert n.tla3bny_competition_topic(comp.id) in topics
    assert n.tla3bny_team_follow_topic(h.id) in topics
    assert n.tla3bny_team_follow_topic(a.id) in topics


def test_follow_team_endpoint_validates_and_subscribes(app_db, monkeypatch):
    app, _db = app_db
    from app.services import notifications as n
    monkeypatch.setattr(n, "subscribe_token_to_topic",
                        lambda token, topic: {"topic": topic})
    c = app.test_client()
    tok = "f" * 150  # _push_token requires a plausible 100–400 char FCM token

    ok = c.post("/api/tla3bny/push/follow-team", json={"token": tok, "team_id": 5})
    assert ok.status_code == 200 and ok.get_json()["followed_team"] == 5

    assert c.post("/api/tla3bny/push/follow-team", json={"token": tok}).status_code == 400
    assert c.post("/api/tla3bny/push/follow-team", json={"team_id": 5}).status_code == 400
