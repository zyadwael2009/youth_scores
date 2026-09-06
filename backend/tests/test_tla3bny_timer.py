"""The live match stopwatch state: elapsed = banked seconds + the current running
segment; a stopped/paused timer just reports its banked seconds.
"""

import os
import tempfile
from datetime import timedelta

import pytest


@pytest.fixture()
def app_ctx():
    os.environ.setdefault("FLASK_ENV", "development")
    from app import create_app
    from app.config import DevelopmentConfig

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
    try:
        app = create_app("development")
        with app.app_context():
            yield
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def test_timer_state_running_and_paused(app_ctx):
    from app.models import Tla3bnyMatch
    from app.api.tla3bny.matches import _match_timer_state
    from app.api.tla3bny._helpers import _utcnow

    m = Tla3bnyMatch(timer_started_at=None, timer_elapsed=0)
    assert _match_timer_state(m) == {"running": False, "elapsed_seconds": 0}

    # Paused with banked time.
    m.timer_elapsed = 120
    assert _match_timer_state(m) == {"running": False, "elapsed_seconds": 120}

    # Running: 5s banked + a segment that started 10s ago ≈ 15s.
    m.timer_started_at = _utcnow() - timedelta(seconds=10)
    m.timer_elapsed = 5
    state = _match_timer_state(m)
    assert state["running"] is True
    assert 14 <= state["elapsed_seconds"] <= 17
