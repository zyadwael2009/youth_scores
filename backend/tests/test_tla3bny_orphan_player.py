"""Deleting an academy must not leave a teamless, never-entered player behind as
a still-public profile. Such an orphan is removed with the academy, and the
public player endpoint hides any orphan that slips through — while a player on
another academy's team (a transfer) is kept and stays visible."""

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


def _super_admin_token(db):
    from app.models import Tla3bnyUser
    from app.services import tla3bny_auth as auth
    admin = Tla3bnyUser(username="s", role="super_admin", status="active", password_hash="x")
    db.session.add(admin)
    db.session.commit()
    return auth.generate_token(admin)


def _academy_team_player(db, *, nid="12345678901234", academy="Ac"):
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyPlayer, Tla3bnyPlayerTeam,
        Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    db.session.add(age)
    db.session.flush()
    ac = Tla3bnyAcademy(name=academy, status="approved")
    db.session.add(ac)
    db.session.flush()
    t = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="T")
    db.session.add(t)
    db.session.flush()
    p = Tla3bnyPlayer(name="P", national_id=nid, dob=date(2011, 1, 1))
    db.session.add(p)
    db.session.flush()
    db.session.add(Tla3bnyPlayerTeam(player_id=p.id, team_id=t.id))
    db.session.commit()
    return ac, t, p


def test_deleting_academy_removes_never_entered_orphan(client):
    app, db = client
    from app.models import Tla3bnyPlayer
    ac, _t, p = _academy_team_player(db)
    pid = p.id
    token = _super_admin_token(db)
    c = app.test_client()

    r = c.delete(f"/api/tla3bny/academies/{ac.id}",
                 headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert db.session.get(Tla3bnyPlayer, pid) is None              # orphan removed
    assert c.get(f"/api/tla3bny/players/{pid}").status_code == 404  # and gone from the API


def test_public_endpoint_hides_a_teamless_never_entered_player(client):
    app, db = client
    from app.models import Tla3bnyPlayerTeam
    _ac, _t, p = _academy_team_player(db)
    pid = p.id
    # Close the membership → on no team now, and never entered a competition.
    m = Tla3bnyPlayerTeam.query.filter_by(player_id=pid).first()
    m.end_date = date(2020, 1, 1)
    db.session.commit()
    c = app.test_client()
    assert c.get(f"/api/tla3bny/players/{pid}").status_code == 404


def test_player_on_another_academys_team_is_kept_and_visible(client):
    app, db = client
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyPlayer, Tla3bnyPlayerTeam,
        Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    db.session.add(age)
    db.session.flush()
    a1 = Tla3bnyAcademy(name="A1", status="approved")
    a2 = Tla3bnyAcademy(name="A2", status="approved")
    db.session.add_all([a1, a2])
    db.session.flush()
    t1 = Tla3bnyTeam(academy_id=a1.id, age_category_id=age.id, name="T1")
    t2 = Tla3bnyTeam(academy_id=a2.id, age_category_id=age.id, name="T2")
    db.session.add_all([t1, t2])
    db.session.flush()
    p = Tla3bnyPlayer(name="P", national_id="12345678901234", dob=date(2011, 1, 1))
    db.session.add(p)
    db.session.flush()
    db.session.add_all([
        Tla3bnyPlayerTeam(player_id=p.id, team_id=t1.id, end_date=date(2020, 1, 1)),  # old, in A1
        Tla3bnyPlayerTeam(player_id=p.id, team_id=t2.id),                              # current, in A2
    ])
    db.session.commit()
    pid = p.id
    token = _super_admin_token(db)
    c = app.test_client()

    r = c.delete(f"/api/tla3bny/academies/{a1.id}",
                 headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert db.session.get(Tla3bnyPlayer, pid) is not None            # kept — still on A2's team
    assert c.get(f"/api/tla3bny/players/{pid}").status_code == 200   # and visible
