"""A clerk is data-entry only: the destructive/structural entry endpoints
(delete a match, bulk-edit, merge players/coaches) require at least `editor`,
while ordinary result entry stays open to a clerk. Locks the role floor from
the platform audit (M2).

NB: requests are made OUTSIDE the setup app-context so each gets its own request
context — current_admin() caches the resolved user on `g`, so sharing one
context across two differently-authed requests would leak the first user.
"""

import os
import tempfile

import pytest

# Destructive / structural — clerk must be blocked (403), editor must pass the gate.
DESTRUCTIVE = [
    ("PATCH", "/api/admin/matches/bulk", {"match_ids": [], "venue": "x"}),
    ("DELETE", "/api/admin/matches/999999", None),
    ("POST", "/api/admin/players/999998/merge-into/999999", None),
    ("POST", "/api/admin/coaches/999998/merge-into/999999", None),
]


@pytest.fixture()
def app_ctx():
    os.environ.setdefault("FLASK_ENV", "development")
    from app import create_app
    from app.config import DevelopmentConfig
    from app.extensions import db

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
    app = create_app("development")
    with app.app_context():
        db.create_all()
        from app.models import AdminUser
        from app.services import auth

        clerk = AdminUser(username="c", role="clerk", is_active=True, password_hash="x")
        editor = AdminUser(username="e", role="editor", is_active=True, password_hash="x")
        db.session.add_all([clerk, editor])
        db.session.commit()
        tokens = {
            "clerk": auth.generate_token(clerk),
            "editor": auth.generate_token(editor),
        }
    try:
        yield app, tokens  # app-context is closed here — requests get fresh ones
    finally:
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _req(client, method, path, body, token):
    return client.open(
        path, method=method, json=body,
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.mark.parametrize("method,path,body", DESTRUCTIVE)
def test_clerk_blocked_from_destructive(app_ctx, method, path, body):
    app, tok = app_ctx
    c = app.test_client()
    # Clerk: rejected by the role gate.
    assert _req(c, method, path, body, tok["clerk"]).status_code == 403
    # Editor: passes the gate (a later 404/400 for the missing entity still
    # proves auth passed — it is not an auth rejection).
    assert _req(c, method, path, body, tok["editor"]).status_code not in (401, 403)


def test_clerk_still_allowed_ordinary_data_entry(app_ctx):
    app, tok = app_ctx
    c = app.test_client()
    # Editing a match is data entry — a clerk must NOT be blocked (404 = the
    # match is missing, i.e. auth passed and the handler ran).
    r = _req(c, "PATCH", "/api/admin/matches/999999", {"status": "live"}, tok["clerk"])
    assert r.status_code not in (401, 403)
