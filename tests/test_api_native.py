import io
from urllib.parse import urlsplit

import pytest
from PIL import Image

from db import File


def _path(url):
    """Reduce an _external url_for(...) result to a client-usable path+query."""
    parts = urlsplit(url)
    return parts.path + (("?" + parts.query) if parts.query else "")


def _upload(client, api_key, data=b"hello world", filename="hello.txt"):
    return client.post(
        "/upload",
        data={"k": api_key, "f": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


def test_upload_requires_api_key(client):
    resp = client.post("/upload", data={}, content_type="multipart/form-data")
    assert resp.status_code == 403
    assert resp.get_json()["status"] == "not authorized"


def test_upload_bad_api_key(client):
    resp = _upload(client, "nope")
    assert resp.status_code == 403


def test_upload_success_creates_file_and_is_downloadable(client, make_user):
    user = make_user()
    resp = _upload(client, user.api_key, b"hello world", "hello.txt")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "share_url" in body and "delete_url" in body

    assert File.select().where(File.user == user).count() == 1

    dl = client.get(_path(body["share_url"]))
    assert dl.status_code == 200
    assert dl.data == b"hello world"
    assert "hello.txt" in dl.headers["Content-Disposition"]


def test_download_wrong_key_and_unknown_id_404(client, make_user):
    user = make_user()
    body = _upload(client, user.api_key).get_json()
    share_path = urlsplit(body["share_url"]).path  # /<b62>/<key>.ext
    b62 = share_path.strip("/").split("/")[0]

    assert client.get("/%s/wrongkey" % b62).status_code == 404
    assert client.get("/zzzzzz/whatever").status_code == 404


def test_thumbnail_generation_for_image(client, make_user):
    user = make_user()
    buf = io.BytesIO()
    Image.new("RGB", (128, 96), "red").save(buf, format="PNG")
    body = _upload(client, user.api_key, buf.getvalue(), "pic.png").get_json()

    resp = client.get(_path(body["share_url"]) + "?thumb")
    assert resp.status_code == 200
    assert resp.mimetype == "image/png"
    thumb = Image.open(io.BytesIO(resp.data))
    assert max(thumb.size) <= 64


def test_delete_removes_file(client, make_user):
    user = make_user()
    body = _upload(client, user.api_key).get_json()

    bad = body["delete_url"].rsplit("/", 1)[0] + "/wrongkey"
    assert client.get(_path(bad)).status_code == 404

    deleted = client.get(_path(body["delete_url"]))
    assert deleted.status_code == 200
    assert deleted.get_json()["status"] == "pshuu~"
    assert client.get(_path(body["share_url"])).status_code == 404


def test_list_requires_key_and_respects_pagination(client, make_user):
    user = make_user()

    assert client.get("/list").status_code == 403

    for i in range(3):
        _upload(client, user.api_key, b"x", "f%d.txt" % i)

    full = client.get("/list", query_string={"k": user.api_key})
    assert full.status_code == 200
    payload = full.get_json()
    assert payload["status"] == "pshuu~"
    assert len(payload["files"]) == 3

    limited = client.get(
        "/list", query_string={"k": user.api_key, "limit": 1}
    )
    assert len(limited.get_json()["files"]) == 1
