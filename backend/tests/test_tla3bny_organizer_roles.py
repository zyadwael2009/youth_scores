"""Per-competition organizer roles: collaborator (full) vs data_entry (match
data only, no approvals, no notifications, chat optional).

Covers the authorization helpers and the two endpoints a data-entry organizer
should and shouldn't reach (enter a match result vs approve a player), plus the
notification-subscription split.
"""

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
    """A competition + sub-competition, two entered teams with a scheduled match,
    an academy with a pending player, plus a collaborator and a data-entry
    organizer login. Returns the ids and tokens the tests drive."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyCompetitionAdmin,
        Tla3bnyCompetitionAge, Tla3bnyCompetitionPlayer, Tla3bnyCompetitionTeam,
        Tla3bnyMatch, Tla3bnyPlayer, Tla3bnySeason, Tla3bnyTeam, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2012", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    cage = Tla3bnyCompetitionAge(competition_id=comp.id, age_category_id=age.id)
    db.session.add(cage)
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    home = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="H")
    away = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="A")
    db.session.add_all([home, away])
    db.session.flush()
    entry = Tla3bnyCompetitionTeam(
        competition_id=comp.id, team_id=home.id, age_category_id=age.id, status="active")
    db.session.add(entry)
    db.session.flush()
    player = Tla3bnyPlayer(name="P", dob=date(2012, 1, 1), national_id="29001011234567")
    db.session.add(player)
    db.session.flush()
    cp = Tla3bnyCompetitionPlayer(
        competition_team_id=entry.id, player_id=player.id, status="pending")
    match = Tla3bnyMatch(
        competition_id=comp.id, age_category_id=age.id,
        home_team_id=home.id, away_team_id=away.id, status="scheduled")
    db.session.add_all([cp, match])
    # Owner + collaborator + data-entry organizers.
    collab = Tla3bnyUser(username="collab", role="competition_admin", status="active",
                         password_hash="x")
    de = Tla3bnyUser(username="de", role="competition_admin", status="active",
                     password_hash="x")
    db.session.add_all([collab, de])
    db.session.flush()
    db.session.add_all([
        Tla3bnyCompetitionAdmin(competition_id=comp.id, user_id=collab.id,
                                is_owner=True, role="collaborator"),
        Tla3bnyCompetitionAdmin(competition_id=comp.id, user_id=de.id,
                                role="data_entry"),
    ])
    db.session.commit()
    return {
        "comp_id": comp.id, "match_id": match.id, "cp_id": cp.id,
        "collab": auth.generate_token(collab), "de": auth.generate_token(de),
        "collab_uid": collab.id, "de_uid": de.id,
    }


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_data_entry_can_enter_a_match_result(client):
    app, db = client
    s = _seed(db)
    r = app.test_client().post(
        f"/api/tla3bny/matches/{s['match_id']}/result",
        json={"home_score": 2, "away_score": 1, "status": "finished"},
        headers=_hdr(s["de"]))
    assert r.status_code in (200, 201), r.get_data(as_text=True)


def test_data_entry_cannot_approve_a_player(client):
    app, db = client
    s = _seed(db)
    r = app.test_client().post(
        f"/api/tla3bny/competition-players/{s['cp_id']}/approve",
        json={}, headers=_hdr(s["de"]))
    assert r.status_code == 403


def test_collaborator_can_approve_a_player(client):
    app, db = client
    s = _seed(db)
    # force=true skips the missing-documents guard — here we're checking that the
    # collaborator is authorized to approve at all, not the paperwork rule.
    r = app.test_client().post(
        f"/api/tla3bny/competition-players/{s['cp_id']}/approve",
        json={"force": True}, headers=_hdr(s["collab"]))
    assert r.status_code in (200, 201), r.get_data(as_text=True)


def test_auth_helpers_split_by_role(client):
    from app.models import Tla3bnyUser
    from app.services import tla3bny_auth as auth
    app, db = client
    s = _seed(db)
    collab = Tla3bnyUser.query.get(s["collab_uid"])
    de = Tla3bnyUser.query.get(s["de_uid"])
    cid = s["comp_id"]
    # Full-organizer gate: collaborator yes, data-entry no.
    assert auth.is_competition_admin(collab, cid) is True
    assert auth.is_competition_admin(de, cid) is False
    # Match-data gate: both yes.
    assert auth.can_enter_match_data(collab, cid) is True
    assert auth.can_enter_match_data(de, cid) is True


def test_data_entry_is_not_subscribed_to_admin_notifications(client):
    app, db = client
    s = _seed(db)
    # A device subscribe pulls the topics for the logged-in user; the data-entry
    # organizer must not get the competition's admin topic.
    from flask import g
    from app.services import notifications
    admin_topic = notifications.tla3bny_compadmin_topic(s["comp_id"])
    # The endpoint's abuse guard wants a plausibly-long FCM token (100–400 chars).
    tok_a, tok_b = "a" * 152, "b" * 152

    def subscribe(tok, auth_tok):
        # current_user() caches on Flask's `g`, which the test fixture's single
        # app context shares across client calls; clear it so each request
        # resolves its own user (in production every request has a fresh context).
        g.pop("tla3bny_user", None)
        return app.test_client().post(
            "/api/tla3bny/push/subscribe-account",
            json={"token": tok}, headers=_hdr(auth_tok)).get_json().get("subscribed", {})

    # The data-entry organizer must NOT get the competition's admin topic…
    assert admin_topic not in subscribe(tok_a, s["de"])
    # …but the collaborator is subscribed to it.
    assert admin_topic in subscribe(tok_b, s["collab"])
