"""The public /uploads/<path> route must never serve a file under uploads/private/
(minors' registration documents). A raw ``startswith("private/")`` check is
bypassable with ``.``/``..`` segments that collapse back into private/ once
send_from_directory resolves them — these tests lock the normalized guard in.
"""

import os

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app("development")  # DEBUG → serves from UPLOAD_FOLDER
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    os.makedirs(tmp_path / "private", exist_ok=True)
    (tmp_path / "private" / "doc.txt").write_text("SECRET")
    os.makedirs(tmp_path / "pub", exist_ok=True)
    (tmp_path / "pub" / "img.txt").write_text("PUBLIC")
    return app.test_client()


@pytest.mark.parametrize(
    "path",
    [
        "/uploads/private/doc.txt",                 # direct
        "/uploads/x/../private/doc.txt",            # raw ..
        "/uploads/x/%2e%2e/private/doc.txt",        # url-encoded ..
        "/uploads/./private/doc.txt",               # leading ./
        "/uploads/%2e/private/doc.txt",             # url-encoded ./
        "/uploads/a/b/../../private/doc.txt",       # deeper traversal
        "/uploads/private\\doc.txt",                # backslash separator
    ],
)
def test_private_uploads_are_never_served(client, path):
    r = client.get(path)
    assert r.status_code == 404, path
    assert b"SECRET" not in r.data, path


def test_public_uploads_still_serve(client):
    r = client.get("/uploads/pub/img.txt")
    assert r.status_code == 200
    assert r.data == b"PUBLIC"
