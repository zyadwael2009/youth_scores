"""Per-entity WhatsApp/OG share cards for the tla3bny app: each builder names the
item and points at its logo/photo so a shared …?id=<id> link previews it."""

import os
import tempfile
from datetime import date

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
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCoach, Tla3bnyCompetition,
        Tla3bnyMatch, Tla3bnyPlayer, Tla3bnySeason, Tla3bnyTeam,
    )
    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="أكاديمية النصر", name_en="Al Nasr", status="approved",
                        logo_path="uploads/nasr.png", description="أفضل أكاديمية")
    db.session.add(ac)
    db.session.flush()
    home = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="النصر أ")
    away = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="الأهلي")
    db.session.add_all([home, away])
    db.session.flush()
    coach = Tla3bnyCoach(team_id=home.id, name="كابتن أحمد", role_ar="مدير فني")
    player = Tla3bnyPlayer(name="محمد صلاح", position="مهاجم", dob=date(2011, 6, 1),
                           photo_path="uploads/player.jpg")
    comp = Tla3bnyCompetition(name="دوري الأكاديميات", season_id=season.id,
                              status="active", logo_path="uploads/cup.png")
    db.session.add_all([coach, player, comp])
    db.session.flush()
    m = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id, home_team_id=home.id,
                     away_team_id=away.id, home_score=3, away_score=1, status="finished",
                     round="1")
    db.session.add(m)
    db.session.commit()
    return {"academy": ac.id, "home": home.id, "coach": coach.id,
            "player": player.id, "competition": comp.id, "match": m.id}


def test_entity_share_meta_builders(app_db):
    _app, db = app_db
    import app as app_pkg
    ids = _seed(db)

    academy = app_pkg._tla3bny_academy_share_meta(ids["academy"])
    assert academy["title"] == "أكاديمية النصر"
    assert academy["image"] == "/uploads/nasr.png" and academy["image_is_logo"] is True

    team = app_pkg._tla3bny_team_share_meta(ids["home"])
    assert team["title"] == "النصر أ"
    assert team["image"] == "/uploads/nasr.png"  # the academy crest

    coach = app_pkg._tla3bny_coach_share_meta(ids["coach"])
    assert coach["title"] == "كابتن أحمد" and coach["description"] == "مدير فني"
    assert "image_is_logo" not in coach  # a real photo is served directly, not flattened

    player = app_pkg._tla3bny_player_share_meta(ids["player"])
    assert player["title"] == "محمد صلاح"
    assert "مهاجم" in player["description"] and "2011" in player["description"]
    assert player["image"] == "/uploads/player.jpg"

    comp = app_pkg._tla3bny_competition_share_meta(ids["competition"])
    assert comp["title"] == "دوري الأكاديميات"
    assert comp["image"] == "/uploads/cup.png" and comp["image_is_logo"] is True

    match = app_pkg._tla3bny_match_share_meta(ids["match"])
    assert match["title"] == "النصر أ 3 - 1 الأهلي"
    assert "دوري الأكاديميات" in match["description"] and "الجولة 1" in match["description"]


def test_missing_entity_returns_none(app_db):
    import app as app_pkg
    assert app_pkg._tla3bny_player_share_meta(999999) is None
    assert app_pkg._tla3bny_match_share_meta(999999) is None


def test_unscored_match_uses_the_cross_form(app_db):
    _app, db = app_db
    from app.models import (
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyMatch,
        Tla3bnySeason, Tla3bnyTeam,
    )
    import app as app_pkg
    age = Tla3bnyAgeCategory(label="2010", sort_order=0)
    season = Tla3bnySeason(name="2026-2027")
    db.session.add_all([age, season])
    db.session.flush()
    ac = Tla3bnyAcademy(name="Ac", status="approved")
    db.session.add(ac)
    db.session.flush()
    h = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="H")
    a = Tla3bnyTeam(academy_id=ac.id, age_category_id=age.id, name="A")
    db.session.add_all([h, a])
    db.session.flush()
    comp = Tla3bnyCompetition(name="C", season_id=season.id, status="active")
    db.session.add(comp)
    db.session.flush()
    m = Tla3bnyMatch(competition_id=comp.id, age_category_id=age.id,
                     home_team_id=h.id, away_team_id=a.id, status="scheduled")
    db.session.add(m)
    db.session.commit()
    meta = app_pkg._tla3bny_match_share_meta(m.id)
    assert meta["title"] == "H × A"  # no score yet
