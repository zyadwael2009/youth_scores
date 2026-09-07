"""Authorization matrix for the organizer-only mutating endpoints.

The audit flagged inline per-route auth checks as the place a new endpoint forgets a
guard. This drives each sensitive endpoint across roles: anonymous, an academy login,
and a competition_admin of a DIFFERENT competition must all be rejected (401/403); the
competition's own admin must pass the auth gate (any non-4xx-auth outcome).
"""

import os
import tempfile

import pytest

# (method, path template, minimal body). {comp}/{match} filled from the seed. Bodies
# are only enough to reach the guard — a later 400/409 still proves auth passed.
ENDPOINTS = [
    ("POST", "/competitions/{comp}/teams", {"team_id": 0}),
    ("POST", "/matches", {"competition_id": "{comp}"}),
    ("PUT", "/matches/{match}", {"status": "live"}),
    ("DELETE", "/matches/{match}", None),
    ("POST", "/matches/{match}/result", {"home_score": 1, "away_score": 0}),
    ("POST", "/competitions/{comp}/punishments",
     {"punishment_type": "point_deduction", "team_id": 0, "points": 1}),
    ("POST", "/competitions/{comp}/awards", {"award_type": "champion", "team_id": 0}),
]


@pytest.fixture()
def ctx():
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
        Tla3bnyAcademy, Tla3bnyAgeCategory, Tla3bnyCompetition, Tla3bnyCompetitionAdmin,
        Tla3bnyCompetitionAge, Tla3bnyMatch, Tla3bnySeason, Tla3bnyTeam, Tla3bnyUser,
    )
    from app.services import tla3bny_auth as auth

    age = Tla3bnyAgeCategory(label="2011", sort_order=0)
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
    comp1 = Tla3bnyCompetition(name="Target", season_id=season.id, status="active")
    comp2 = Tla3bnyCompetition(name="Other", season_id=season.id, status="active")
    db.session.add_all([comp1, comp2])
    db.session.flush()
    db.session.add(Tla3bnyCompetitionAge(competition_id=comp1.id, age_category_id=age.id))
    match = Tla3bnyMatch(competition_id=comp1.id, age_category_id=age.id,
                         home_team_id=h.id, away_team_id=a.id, status="scheduled")
    db.session.add(match)
    # Users.
    su = Tla3bnyUser(username="su", role="super_admin", status="active", password_hash="x")
    admin1 = Tla3bnyUser(username="a1", role="competition_admin", status="active", password_hash="x")
    admin2 = Tla3bnyUser(username="a2", role="competition_admin", status="active", password_hash="x")
    acad = Tla3bnyUser(username="ac", role="academy", status="active", password_hash="x", academy_id=ac.id)
    db.session.add_all([su, admin1, admin2, acad])
    db.session.flush()
    db.session.add(Tla3bnyCompetitionAdmin(competition_id=comp1.id, user_id=admin1.id))
    db.session.add(Tla3bnyCompetitionAdmin(competition_id=comp2.id, user_id=admin2.id))
    db.session.commit()
    return {
        "comp": comp1.id, "match": match.id, "team": h.id,
        "admin1": auth.generate_token(admin1),   # runs THIS competition
        "admin2": auth.generate_token(admin2),   # runs a DIFFERENT competition
        "academy": auth.generate_token(acad),
    }


def _resolve(spec, s):
    method, path, body = spec
    path = path.format(comp=s["comp"], match=s["match"])
    if isinstance(body, dict):
        body = {k: (s["comp"] if v == "{comp}" else v) for k, v in body.items()}
    return method, path, body


def _call(c, method, path, body, token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    fn = {"POST": c.post, "PUT": c.put, "DELETE": c.delete}[method]
    return fn(f"/api/tla3bny{path}", json=body, headers=headers)


@pytest.mark.parametrize("spec", ENDPOINTS, ids=[f"{m} {p}" for m, p, _ in ENDPOINTS])
@pytest.mark.parametrize("who", ["anon", "academy", "other_admin"])
def test_unauthorized_callers_are_rejected(ctx, spec, who):
    app, db = ctx
    s = _seed(db)
    method, path, body = _resolve(spec, s)
    token = None if who == "anon" else s["academy"] if who == "academy" else s["admin2"]
    r = _call(app.test_client(), method, path, body, token)
    assert r.status_code in (401, 403), (
        f"{who} reached {method} {path} (status {r.status_code}) — guard missing?")


@pytest.mark.parametrize("spec", ENDPOINTS, ids=[f"{m} {p}" for m, p, _ in ENDPOINTS])
def test_the_competitions_own_admin_passes_the_guard(ctx, spec):
    app, db = ctx
    s = _seed(db)
    method, path, body = _resolve(spec, s)
    r = _call(app.test_client(), method, path, body, s["admin1"])
    # It may 400/409 on the minimal body, but must NOT be blocked at the auth layer.
    assert r.status_code not in (401, 403), (
        f"the competition's own admin was blocked from {method} {path} ({r.status_code})")
