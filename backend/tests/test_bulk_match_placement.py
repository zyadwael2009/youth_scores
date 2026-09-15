"""Stage / group placement for matches — the bulk endpoint (file a whole
imported round under its real stage/group) and the single-match PATCH that the
match editor's "الدور والمجموعة" panel drives. Pins the placement rules:
same-competition only, group-belongs-to-stage, and the duplicate-fixture skip.
"""

import os
import tempfile
from datetime import date, datetime

os.environ.setdefault("FLASK_ENV", "development")

from app import create_app
from app.config import DevelopmentConfig
from app.extensions import db


def _setup():
    """One competition with a league stage (1) and a knockout stage (2) that has
    a group, two enrolled teams, and one match sitting in the league stage. Plus
    a SECOND competition (its own stage) to prove a cross-competition move is
    refused. Returns (app, ctx dict of ids, editor auth header)."""
    tmpdb = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmpdb.close()
    _orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmpdb.name}"
    try:
        app = create_app("development")
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = _orig
    with app.app_context():
        from app.models import (
            AdminUser, AgeGroup, Club, Team, Season, Competition, Stage, Group,
            CompetitionTeam, Match,
        )
        from app.services import auth

        db.create_all()

        ag = AgeGroup(name_ar="تحت 17", name_en="U17", oldest_birth_year=2009)
        c1 = Club(name_ar="الأهلي", name_en="Ahly")
        c2 = Club(name_ar="الزمالك", name_en="Zamalek")
        db.session.add_all([ag, c1, c2])
        db.session.flush()

        home = Team(club_id=c1.id, age_group_id=ag.id)
        away = Team(club_id=c2.id, age_group_id=ag.id)
        season = Season(name_ar="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        db.session.add_all([home, away, season])
        db.session.flush()

        comp = Competition(season_id=season.id, age_group_id=ag.id, code="c1", name_ar="الدوري")
        other = Competition(season_id=season.id, age_group_id=ag.id, code="c2", name_ar="بطولة أخرى")
        db.session.add_all([comp, other])
        db.session.flush()

        stage1 = Stage(competition_id=comp.id, stage_order=1, type="league")
        stage2 = Stage(competition_id=comp.id, stage_order=2, type="knockout")
        other_stage = Stage(competition_id=other.id, stage_order=1, type="league")
        db.session.add_all([stage1, stage2, other_stage])
        db.session.flush()

        group = Group(stage_id=stage2.id, name_ar="المجموعة أ", name_en="Group A")
        db.session.add(group)
        db.session.add_all([
            CompetitionTeam(competition_id=comp.id, team_id=home.id),
            CompetitionTeam(competition_id=comp.id, team_id=away.id),
        ])
        db.session.flush()

        match = Match(
            stage_id=stage1.id, home_team_id=home.id, away_team_id=away.id,
            status="scheduled", match_date=datetime(2026, 3, 1, 15, 0),
        )
        db.session.add(match)
        db.session.flush()

        editor = AdminUser(username="e", role="editor", is_active=True, password_hash="x")
        db.session.add(editor)
        db.session.commit()

        ctx = {
            "match_id": match.id, "stage1_id": stage1.id, "stage2_id": stage2.id,
            "group_id": group.id, "other_stage_id": other_stage.id,
            "home_id": home.id, "away_id": away.id,
        }
        header = {"Authorization": f"Bearer {auth.generate_token(editor)}"}
    return app, ctx, header


def _match(app, mid):
    with app.app_context():
        from app.models import Match
        return db.session.get(Match, mid)


def test_bulk_move_stage_and_group():
    app, ctx, hdr = _setup()
    c = app.test_client()
    r = c.patch("/api/admin/matches/bulk", json={
        "match_ids": [ctx["match_id"]],
        "stage_id": ctx["stage2_id"], "group_id": ctx["group_id"],
    }, headers=hdr)
    assert r.status_code == 200, r.data
    assert r.get_json() == {"updated": 1, "skipped": 0}

    m = _match(app, ctx["match_id"])
    assert m.stage_id == ctx["stage2_id"]
    assert m.group_id == ctx["group_id"]
    # The phase label follows the group, as create / single-edit do.
    assert m.round_label_ar == "المجموعة أ"


def test_bulk_stage_without_group_clears_group():
    app, ctx, hdr = _setup()
    c = app.test_client()
    # First put it in the group…
    c.patch("/api/admin/matches/bulk", json={
        "match_ids": [ctx["match_id"]],
        "stage_id": ctx["stage2_id"], "group_id": ctx["group_id"],
    }, headers=hdr)
    # …then re-assign to the same stage with no group → group cleared.
    r = c.patch("/api/admin/matches/bulk", json={
        "match_ids": [ctx["match_id"]], "stage_id": ctx["stage2_id"], "group_id": None,
    }, headers=hdr)
    assert r.status_code == 200, r.data
    assert _match(app, ctx["match_id"]).group_id is None


def test_bulk_skips_duplicate_pairing_in_target_stage():
    app, ctx, hdr = _setup()
    # A match with the SAME pair already lives in the target stage.
    with app.app_context():
        from app.models import Match
        db.session.add(Match(
            stage_id=ctx["stage2_id"], home_team_id=ctx["home_id"],
            away_team_id=ctx["away_id"], status="scheduled",
        ))
        db.session.commit()

    c = app.test_client()
    r = c.patch("/api/admin/matches/bulk", json={
        "match_ids": [ctx["match_id"]], "stage_id": ctx["stage2_id"],
    }, headers=hdr)
    assert r.status_code == 200, r.data
    assert r.get_json() == {"updated": 0, "skipped": 1}
    # The source match is left untouched in its original stage.
    assert _match(app, ctx["match_id"]).stage_id == ctx["stage1_id"]


def test_bulk_rejects_stage_in_another_competition():
    app, ctx, hdr = _setup()
    c = app.test_client()
    r = c.patch("/api/admin/matches/bulk", json={
        "match_ids": [ctx["match_id"]], "stage_id": ctx["other_stage_id"],
    }, headers=hdr)
    assert r.status_code == 400
    assert _match(app, ctx["match_id"]).stage_id == ctx["stage1_id"]


def test_bulk_rejects_group_not_in_stage():
    app, ctx, hdr = _setup()
    c = app.test_client()
    # Group belongs to stage2, but we target stage1 → mismatch, rejected.
    r = c.patch("/api/admin/matches/bulk", json={
        "match_ids": [ctx["match_id"]],
        "stage_id": ctx["stage1_id"], "group_id": ctx["group_id"],
    }, headers=hdr)
    assert r.status_code == 400
    assert _match(app, ctx["match_id"]).stage_id == ctx["stage1_id"]


def test_single_match_patch_sets_stage_and_group():
    """The match editor's stage/group panel PATCHes the single-match endpoint —
    which previously dropped stage_id/group_id silently."""
    app, ctx, hdr = _setup()
    c = app.test_client()
    r = c.patch(f"/api/admin/matches/{ctx['match_id']}", json={
        "stage_id": ctx["stage2_id"], "group_id": ctx["group_id"],
    }, headers=hdr)
    assert r.status_code == 200, r.data
    m = _match(app, ctx["match_id"])
    assert m.stage_id == ctx["stage2_id"]
    assert m.group_id == ctx["group_id"]
