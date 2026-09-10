"""Admin-controlled group order: new groups append, ▲▼ (the /move endpoint)
swaps a group with its neighbour, and the standings group order follows it —
so groups show in the arranged order, not «المجموعة 10» before «المجموعة 2»."""

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
            yield app, db
            db.session.remove()
            db.engine.dispose()
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _seed_group_stage(db):
    from app.models import (
        Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyCompetitionAge,
        Tla3bnySeason, Tla3bnyStage, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    cage = Tla3bnyCompetitionAge(competition_id=comp.id, age_category_id=age.id)
    db.session.add(cage)
    db.session.flush()
    stage = Tla3bnyStage(competition_age_id=cage.id, name="Groups", stage_order=1, type="group")
    admin = Tla3bnyUser(username="s", role="super_admin", status="active", password_hash="x")
    db.session.add_all([stage, admin])
    db.session.commit()
    return {"cage": cage, "stage_id": stage.id, "token": auth.generate_token(admin)}


def test_create_appends_and_move_reorders_and_standings_follow(client):
    app, db = client
    from app.models import Tla3bnyGroup
    from app.services import tla3bny_tables as tables

    s = _seed_group_stage(db)
    c = app.test_client()
    hdr = {"Authorization": f"Bearer {s['token']}"}

    # New groups append at the end: 0, 1, 2.
    ids = []
    for nm in ("A", "B", "C"):
        r = c.post(f"/api/tla3bny/stages/{s['stage_id']}/groups", json={"name": nm}, headers=hdr)
        assert r.status_code == 201
        ids.append(r.get_json()["id"])
    assert [db.session.get(Tla3bnyGroup, gid).sort_order for gid in ids] == [0, 1, 2]

    # Standings order follows sort_order (A, B, C).
    assert [g.id for g in tables.groups_of(s["cage"])] == ids

    # Move C up → swaps with B → A, C, B.
    r = c.post(f"/api/tla3bny/groups/{ids[2]}/move", json={"direction": "up"}, headers=hdr)
    assert r.status_code == 200
    db.session.expire_all()
    assert [g.id for g in tables.groups_of(s["cage"])] == [ids[0], ids[2], ids[1]]

    # Moving the top group up is a harmless no-op.
    r = c.post(f"/api/tla3bny/groups/{ids[0]}/move", json={"direction": "up"}, headers=hdr)
    assert r.status_code == 200
    db.session.expire_all()
    assert [g.id for g in tables.groups_of(s["cage"])] == [ids[0], ids[2], ids[1]]


def test_move_requires_a_valid_direction(client):
    app, db = client
    s = _seed_group_stage(db)
    c = app.test_client()
    hdr = {"Authorization": f"Bearer {s['token']}"}
    gid = c.post(f"/api/tla3bny/stages/{s['stage_id']}/groups", json={"name": "A"},
                 headers=hdr).get_json()["id"]
    assert c.post(f"/api/tla3bny/groups/{gid}/move", json={"direction": "sideways"},
                  headers=hdr).status_code == 400
