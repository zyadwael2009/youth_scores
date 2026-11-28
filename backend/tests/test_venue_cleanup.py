"""Venue cleanup: grouping free-text match venues, linking them to the directory
(reversibly — typed text is never rewritten), and merging duplicate venues."""

import os
import tempfile
from datetime import date, datetime

os.environ.setdefault("FLASK_ENV", "development")

from app import create_app
from app.config import DevelopmentConfig
from app.extensions import db
from app.services import venue_names as vn


# ── grouping ─────────────────────────────────────────────────────────────────

def test_spelling_variants_group_under_the_most_used_name():
    groups, _ = vn.group_names({
        "بلاك ستار ٢": 218, "بلك ستار ٢": 12, "ملعب بلاك ستار ٢": 10, "بلاك ستار٢": 1,
        "نادى طلانع الفرسان": 31, "طلائع الفرسان": 31, "طانع الفرسان": 6,
        "انبي - الكيلو 17": 48, "انبي الكيلو ١٧": 20,
    })
    as_sets = [set(g) for g in groups]
    assert {"بلاك ستار ٢", "بلك ستار ٢", "ملعب بلاك ستار ٢", "بلاك ستار٢"} in as_sets
    assert {"نادى طلانع الفرسان", "طلائع الفرسان", "طانع الفرسان"} in as_sets
    assert {"انبي - الكيلو 17", "انبي الكيلو ١٧"} in as_sets
    assert groups[0][0] == "بلاك ستار ٢"  # biggest group first, main spelling first


def test_generic_words_do_not_chain_different_grounds():
    groups, _ = vn.group_names({
        "مركز شباب الاميرية": 119, "مركز شباب زينهم": 85,
        "مركز التنمية الشبابية بالأميرية": 8, "م ش زينهم": 4,
    })
    assert sorted(map(sorted, groups)) == sorted([
        sorted(["مركز شباب الاميرية", "مركز التنمية الشبابية بالأميرية"]),
        sorted(["مركز شباب زينهم", "م ش زينهم"]),
    ])


def test_contained_names_are_only_a_maybe_not_merged():
    groups, maybe = vn.group_names({"دار الوقود": 198, "دار الوقود التجمع الخامس": 20})
    assert len(groups) == 2
    assert maybe == [(0, 1)]


def test_best_venue_matches_the_directory_spelling():
    venues = [(1, "استاد السلام", None), (2, "نادي بلاك ستار 2", "Black Star 2")]
    assert vn.best_venue(["بلك ستار ٢"], venues) == 2
    assert vn.best_venue(["مكان غير معروف"], venues) is None


# ── endpoints ────────────────────────────────────────────────────────────────

def _setup():
    tmpdb = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmpdb.close()
    _orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmpdb.name}"
    try:
        app = create_app("development")
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = _orig
    with app.app_context():
        from app.models import (AdminUser, AgeGroup, Club, Competition, Match, Season,
                                Stage, Team, Venue)
        from app.services import auth

        db.create_all()
        ag = AgeGroup(name_ar="تحت 17", name_en="U17", oldest_birth_year=2009)
        c1, c2 = Club(name_ar="أ"), Club(name_ar="ب")
        db.session.add_all([ag, c1, c2])
        db.session.flush()
        home, away = Team(club_id=c1.id, age_group_id=ag.id), Team(club_id=c2.id, age_group_id=ag.id)
        season = Season(name_ar="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        db.session.add_all([home, away, season])
        db.session.flush()
        comp = Competition(season_id=season.id, age_group_id=ag.id, code="c1", name_ar="الدوري")
        db.session.add(comp)
        db.session.flush()
        stage = Stage(competition_id=comp.id, stage_order=1, type="league")
        db.session.add(stage)
        db.session.flush()

        def m(venue_ar, deleted=False):
            return Match(stage_id=stage.id, home_team_id=home.id, away_team_id=away.id,
                         status="scheduled", match_date=datetime(2026, 3, 1, 15, 0),
                         venue_ar=venue_ar,
                         deleted_at=datetime(2026, 3, 2) if deleted else None)

        db.session.add_all([
            m("بلاك ستار ٢"), m("بلاك ستار ٢"), m(" بلك ستار ٢ "), m("بلك ستار ٢", deleted=True),
            m("دار الوقود"), m(None),
        ])
        v1 = Venue(name_ar="بلاك ستار 2", url="https://maps.example/bs")
        v2 = Venue(name_ar="بلاك ستار (مكرر)")
        editor = AdminUser(username="e", role="editor", is_active=True, password_hash="x")
        db.session.add_all([v1, v2, editor])
        db.session.commit()
        ids = {"v1": v1.id, "v2": v2.id}
        hdr = {"Authorization": f"Bearer {auth.generate_token(editor)}"}
    return app, ids, hdr


def _venue_ids(app):
    with app.app_context():
        from app.models import Match
        return sorted((m.venue_ar or "", m.venue_id or 0)
                      for m in Match.query.filter(Match.deleted_at.is_(None)).all())


def test_listing_groups_spellings_and_suggests_the_directory_venue():
    app, ids, hdr = _setup()
    r = app.test_client().get("/api/admin/venue-cleanup", headers=hdr)
    assert r.status_code == 200, r.data
    d = r.get_json()
    assert d["stats"] == {"matches": 4, "linked": 0, "spellings": 3, "groups": 2}
    g = d["groups"][0]
    assert g["main"] == "بلاك ستار ٢" and g["total"] == 3   # deleted match not counted
    assert {s["text"] for s in g["spellings"]} == {"بلاك ستار ٢", "بلك ستار ٢"}  # trimmed
    assert g["suggested_venue_id"] == ids["v1"]


def test_link_then_unlink_keeps_the_typed_text():
    app, ids, hdr = _setup()
    c = app.test_client()
    before = _venue_ids(app)
    r = c.post("/api/admin/venue-cleanup/link", headers=hdr,
               json={"texts": ["بلاك ستار ٢", "بلك ستار ٢"], "venue_id": ids["v1"]})
    assert r.status_code == 200, r.data
    assert r.get_json()["linked"] == 3
    after = _venue_ids(app)
    assert [t for t, _ in after] == [t for t, _ in before]           # text untouched
    assert sum(1 for _, v in after if v == ids["v1"]) == 3
    with app.app_context():
        from app.models import Match
        assert db.session.query(Match).filter(Match.deleted_at.isnot(None)).one().venue_id is None

    d = c.get("/api/admin/venue-cleanup", headers=hdr).get_json()
    assert d["stats"]["linked"] == 3 and d["groups"][0]["linked"] == 3

    r = c.post("/api/admin/venue-cleanup/unlink", headers=hdr, json={"texts": ["بلك ستار ٢"]})
    assert r.get_json()["unlinked"] == 1


def test_link_to_a_new_venue_creates_it():
    app, _, hdr = _setup()
    r = app.test_client().post("/api/admin/venue-cleanup/link", headers=hdr, json={
        "texts": ["دار الوقود"], "new_venue": {"name_ar": "دار الوقود", "url": ""}})
    assert r.status_code == 200, r.data
    body = r.get_json()
    assert body["linked"] == 1 and body["venue"]["name_ar"] == "دار الوقود"


def test_link_validation():
    app, _, hdr = _setup()
    c = app.test_client()
    assert c.post("/api/admin/venue-cleanup/link", headers=hdr, json={"texts": []}).status_code == 400
    assert c.post("/api/admin/venue-cleanup/link", headers=hdr,
                  json={"texts": ["x"], "venue_id": 999}).status_code == 404
    assert c.post("/api/admin/venue-cleanup/link", headers=hdr,
                  json={"texts": ["x"], "new_venue": {}}).status_code == 400
    assert c.get("/api/admin/venue-cleanup").status_code == 401


def test_merge_moves_matches_and_keeps_the_map_link():
    app, ids, hdr = _setup()
    c = app.test_client()
    c.post("/api/admin/venue-cleanup/link", headers=hdr,
           json={"texts": ["بلاك ستار ٢"], "venue_id": ids["v2"]})
    r = c.post(f"/api/admin/venues/{ids['v1']}/merge", headers=hdr, json={"into": ids["v2"]})
    assert r.status_code == 200, r.data
    assert r.get_json()["venue"]["url"] == "https://maps.example/bs"
    with app.app_context():
        from app.models import Venue
        assert db.session.get(Venue, ids["v1"]) is None
    assert c.post(f"/api/admin/venues/{ids['v2']}/merge", headers=hdr,
                  json={"into": ids["v2"]}).status_code == 400
