"""Results broadcast: a device with no favourites rides TLA3BNY_TOPIC_RESULTS so
every round digest still reaches it, and the round digest fans out to that
broadcast topic alongside the competition's own follow topic."""

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


def test_results_topic_is_namespaced_apart_from_youthscores():
    from app.services import notifications as n
    # Must be tla3bny-namespaced so it never crosses over to youthscores' "results".
    assert n.TLA3BNY_TOPIC_RESULTS == "t3_results"
    assert n.TLA3BNY_TOPIC_RESULTS != n.TOPIC_RESULTS


def test_round_digest_also_hits_the_results_broadcast(app_db, monkeypatch):
    app, db = app_db
    from app.models import Tla3bnyCompetition, Tla3bnySeason
    from app.services import notifications as n

    season = Tla3bnySeason(name="2026-2027")
    db.session.add(season)
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.commit()

    topics = []
    monkeypatch.setattr(n, "send_to_topic",
                        lambda topic, title, body, data=None: topics.append(topic) or {})
    # Two "matches" — only len() is used by the digest body.
    n.notify_tla3bny_round_results(comp, "1", [object(), object()])

    assert n.tla3bny_competition_topic(comp.id) in topics
    assert n.TLA3BNY_TOPIC_RESULTS in topics


def test_results_broadcast_endpoint_subscribes_and_unsubscribes(app_db, monkeypatch):
    app, _db = app_db
    from app.services import notifications as n
    subbed, unsubbed = [], []
    monkeypatch.setattr(n, "subscribe_token_to_topic",
                        lambda token, topic: subbed.append(topic) or {"topic": topic})
    monkeypatch.setattr(n, "unsubscribe_token_from_topic",
                        lambda token, topic: unsubbed.append(topic) or {"topic": topic})
    c = app.test_client()
    tok = "f" * 150  # _push_token requires a plausible 100–400 char FCM token

    join = c.post("/api/tla3bny/push/results-broadcast", json={"token": tok, "subscribe": True})
    assert join.status_code == 200 and join.get_json()["results_broadcast"] is True
    assert n.TLA3BNY_TOPIC_RESULTS in subbed

    leave = c.post("/api/tla3bny/push/results-broadcast", json={"token": tok, "subscribe": False})
    assert leave.status_code == 200 and leave.get_json()["results_broadcast"] is False
    assert n.TLA3BNY_TOPIC_RESULTS in unsubbed

    # Missing/short token is rejected.
    assert c.post("/api/tla3bny/push/results-broadcast", json={"subscribe": True}).status_code == 400
