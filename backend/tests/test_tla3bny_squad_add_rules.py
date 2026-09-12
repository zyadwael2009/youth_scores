"""Rules for adding a player to a team's squad (POST /teams/<id>/players):
a photo is mandatory, a date of birth is mandatory, and the player must not be
older than the team's age bracket (younger is allowed — they may guest up).
"""

import os
import tempfile
from io import BytesIO

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


def _png():
    from PIL import Image
    buf = BytesIO()
    Image.new("RGB", (8, 8), "green").save(buf, "PNG")
    buf.seek(0)
    return buf


def _seed(db):
    """A team whose age bracket is birth-year 2013, entered (approved) in a
    competition so its squad is editable, with a team login."""
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyCompetitionTeam,
        Tla3bnySeason, Tla3bnyTeam, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2013", sort_order=0, oldest_birth_year=2013)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="A", status="approved")
    db.session.add(ac)
    db.session.flush()
    team = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="T")
    db.session.add(team)
    db.session.flush()
    comp = Tla3bnyCompetition(name="Cup", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    db.session.add(Tla3bnyCompetitionTeam(
        competition_id=comp.id, team_id=team.id, age_category_id=age.id, status="active"))
    user = Tla3bnyUser(username="t", role="team", status="active",
                       password_hash="x", team_id=team.id)
    db.session.add(user)
    db.session.commit()
    return team.id, auth.generate_token(user)


def _post(app, team_id, token, *, national_id, dob, with_photo):
    data = {"name": "Kid", "national_id": national_id}
    if dob is not None:
        data["dob"] = dob
    if with_photo:
        data["photo"] = (_png(), "p.png")
    return app.test_client().post(
        f"/api/tla3bny/teams/{team_id}/players",
        data=data, content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"})


def test_photo_is_required(client):
    app, db = client
    team_id, token = _seed(db)
    r = _post(app, team_id, token, national_id="29013011234567", dob="2013-05-01", with_photo=False)
    assert r.status_code == 400


def test_dob_is_required(client):
    app, db = client
    team_id, token = _seed(db)
    r = _post(app, team_id, token, national_id="29013011234567", dob=None, with_photo=True)
    assert r.status_code == 400


def test_player_older_than_team_age_is_rejected(client):
    app, db = client
    team_id, token = _seed(db)
    # Team is birth-year 2013; a 2012-born player is too old.
    r = _post(app, team_id, token, national_id="29012011234567", dob="2012-12-31", with_photo=True)
    assert r.status_code == 400


def test_player_in_or_under_age_is_accepted(client):
    app, db = client
    team_id, token = _seed(db)
    # Same age (2013) is fine…
    r1 = _post(app, team_id, token, national_id="29013011234567", dob="2013-01-01", with_photo=True)
    assert r1.status_code in (200, 201), r1.get_data(as_text=True)
    # …and younger (2014) is fine too (may guest up).
    r2 = _post(app, team_id, token, national_id="21401011234567", dob="2014-06-01", with_photo=True)
    assert r2.status_code in (200, 201), r2.get_data(as_text=True)
