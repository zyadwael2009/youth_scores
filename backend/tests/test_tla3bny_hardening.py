"""Advanced-audit round-1 hardening: the blueprint DB-error safety net and the
URL length cap. (The replace-quota FOR UPDATE fix and the length clips defend against
DataError→session-poisoning, which SQLite can't reproduce — it doesn't enforce
VARCHAR limits — so those are covered by the handler test + code review.)"""

import os
import tempfile

import pytest


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


def test_db_error_handler_rolls_back_and_returns_500(app_ctx):
    app, db = app_ctx
    from sqlalchemy.exc import SQLAlchemyError
    from app.api.tla3bny import _tla3bny_db_error
    from app.models import Tla3bnyAgeCategory

    with app.test_request_context():
        # A pending write that a failed later statement would otherwise leave
        # stranded in a poisoned session.
        db.session.add(Tla3bnyAgeCategory(label="X", sort_order=0))
        resp, status = _tla3bny_db_error(SQLAlchemyError("boom"))
        assert status == 500
        # The handler rolled the session back, so the pending insert is gone and the
        # session is usable again (a query doesn't raise).
        assert Tla3bnyAgeCategory.query.count() == 0


def test_db_error_handler_is_registered_on_the_blueprint(app_ctx):
    app, _db = app_ctx
    from sqlalchemy.exc import SQLAlchemyError

    handlers = app.error_handler_spec.get("tla3bny", {}).get(None, {})
    assert SQLAlchemyError in handlers  # blueprint-scoped safety net is wired


def test_clean_url_caps_length_to_the_column_width():
    from app.api.tla3bny._helpers import _clean_url

    long_bare = "example.com/" + "a" * 2000
    out = _clean_url(long_bare)
    assert out is not None and out.startswith("https://")
    assert len(out) <= 512  # fits the String(512) URL columns, no DataError

    long_http = "http://example.com/" + "b" * 2000
    assert len(_clean_url(long_http)) <= 512

    # Unsafe schemes are still rejected regardless of length.
    assert _clean_url("javascript:alert(1)") is None
    assert _clean_url("") is None
