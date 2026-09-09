"""tla3bny per-news social-share injection.

A /news/?news=<id> link (or the competition page's …&news=<id>) served on the
tla3bny host gets that item's title + cover baked into its Open Graph tags, so
WhatsApp/Telegram show a real preview instead of the one generic card every
static page ships with. Injection is keyed off the ``news`` param and reads the
tla3bny news model (title/body/image_path).
"""

import os
import tempfile

from app.extensions import db

INDEX_HTML = (
    "<html><head><title>generic</title>"
    '<meta name="description" content="generic"/></head><body>x</body></html>'
)

TLA = {"Host": "tla3bny.youthscores.org"}


def _make_app():
    os.environ.setdefault("FLASK_ENV", "development")
    from app import create_app
    from app.config import DevelopmentConfig

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    orig = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp.name}"
    try:
        return create_app("development")
    finally:
        DevelopmentConfig.SQLALCHEMY_DATABASE_URI = orig


def _tla3bny_app_with_news(published=True):
    """App whose tla3bny frontend dir is a temp dir with a minimal /news/ shell,
    plus one Tla3bnyNews row. Returns (app, news_id)."""
    from app.models import Tla3bnyNews

    app = _make_app()
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "news"), exist_ok=True)
    for rel in ("index.html", os.path.join("news", "index.html")):
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(INDEX_HTML)
    app.config["TLA3BNY_FRONTEND_DIR"] = root
    with app.app_context():
        db.create_all()
        n = Tla3bnyNews(
            title="بطولة الصيف",
            body="نص\nالخبر  الطويل",
            image_path="uploads/cover.jpg",
            is_published=published,
        )
        db.session.add(n)
        db.session.commit()
        nid = n.id
    return app, nid


def test_news_link_injects_title_and_image():
    app, nid = _tla3bny_app_with_news()
    r = app.test_client().get(f"/news/?news={nid}", headers=TLA)
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert 'property="og:title" content="بطولة الصيف"' in body
    assert "/uploads/cover.jpg" in body                 # cover absolutized for OG
    assert 'property="og:image"' in body
    assert "<title>بطولة الصيف</title>" in body          # browser-tab title rewritten
    assert "NewsArticle" in body                         # JSON-LD structured data


def test_no_news_param_serves_plain_page():
    app, _ = _tla3bny_app_with_news()
    r = app.test_client().get("/news/", headers=TLA)
    body = r.get_data(as_text=True)
    assert "<title>generic</title>" in body
    assert "og:title" not in body


def test_unpublished_news_not_injected():
    app, nid = _tla3bny_app_with_news(published=False)
    r = app.test_client().get(f"/news/?news={nid}", headers=TLA)
    body = r.get_data(as_text=True)
    assert "<title>generic</title>" in body
    assert "og:title" not in body
