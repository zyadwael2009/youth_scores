"""National-ID uniqueness, end-to-end through the create-player endpoint.

The concurrency fix (a FOR UPDATE lock on the parent row before the check-then-insert)
can't be exercised on SQLite, which ignores row locking — but these tests drive the
full endpoint path including the new locked re-check, so a regression in the duplicate
rejection would be caught. See advanced-audit H3.
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


def _seed_team_login(db):
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyCompetitionTeam,
        Tla3bnySeason, Tla3bnyTeam, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2012", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="A", status="approved")
    db.session.add(ac)
    db.session.flush()
    team = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="T")
    db.session.add(team)
    db.session.flush()
    # Adding squad players now requires the team to be entered in (and approved
    # for) at least one competition, so give it an active entry.
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


def _png():
    """A tiny valid PNG — the squad-add endpoint now requires a real photo."""
    from io import BytesIO
    from PIL import Image
    buf = BytesIO()
    Image.new("RGB", (8, 8), "blue").save(buf, "PNG")
    buf.seek(0)
    return buf


def _add_player(app_client, team_id, token, name, national_id):
    return app_client.post(
        f"/api/tla3bny/teams/{team_id}/players",
        data={"name": name, "national_id": national_id, "dob": "2012-05-01",
              "photo": (_png(), "p.png")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_duplicate_national_id_in_academy_is_rejected(client):
    app, db = client
    c = app.test_client()
    team_id, token = _seed_team_login(db)

    r1 = _add_player(c, team_id, token, "Kid One", "29001011234567")
    assert r1.status_code in (200, 201)

    # Same 14-digit national ID, different name → rejected (the locked re-check path).
    r2 = _add_player(c, team_id, token, "Impostor", "29001011234567")
    assert r2.status_code == 409

    # A different ID is fine.
    r3 = _add_player(c, team_id, token, "Kid Two", "29001011230000")
    assert r3.status_code in (200, 201)


def test_national_id_must_be_present_and_14_digits(client):
    app, db = client
    c = app.test_client()
    team_id, token = _seed_team_login(db)

    assert _add_player(c, team_id, token, "No ID", "").status_code == 400
    assert _add_player(c, team_id, token, "Short", "123").status_code == 400
