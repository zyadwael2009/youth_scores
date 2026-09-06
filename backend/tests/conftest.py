"""Shared test setup.

The tla3bny read endpoints now use an in-process compute cache (app.services.cache)
keyed by ids like ``t3:comp:1``. That store is per-process, not per-test, and every
test builds a fresh DB whose first competition is also id 1 — so without clearing it a
value cached by one test could be served to the next. Clear it around every test.
"""

import pytest


@pytest.fixture(autouse=True)
def _clear_compute_cache():
    from app.services import cache
    cache.clear()
    yield
    cache.clear()
