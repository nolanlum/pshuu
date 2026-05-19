import io
from urllib.parse import urlsplit

import pytest
from PIL import Image

from db import File
from files import FileMapper


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

    # Each entry exposes a b62 id consistent with its raw key.
    for raw_id, entry in payload["files"].items():
        assert FileMapper.b62_decode(entry["id"]) == int(raw_id)

    limited = client.get(
        "/list", query_string={"k": user.api_key, "limit": 1}
    )
    assert len(limited.get_json()["files"]) == 1


def _b62_id(upload_body):
    """Extract the b62 file id from an /upload share_url."""
    return urlsplit(upload_body["share_url"]).path.strip("/").split("/")[0]


def test_delete_own_file_requires_key(client, make_user):
    user = make_user()
    b62 = _b62_id(_upload(client, user.api_key).get_json())

    assert client.post("/delete/%s" % b62).status_code == 403
    assert (
        client.post("/delete/%s" % b62, data={"k": "wrong"}).status_code
        == 403
    )
    # File untouched after failed auth.
    assert File.select().where(File.user == user).count() == 1


def test_delete_own_file_success(client, make_user):
    user = make_user()
    body = _upload(client, user.api_key).get_json()
    b62 = _b62_id(body)

    resp = client.post("/delete/%s" % b62, data={"k": user.api_key})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "pshuu~"
    assert File.select().where(File.user == user).count() == 0
    assert client.get(_path(body["share_url"])).status_code == 404


def test_delete_other_users_file_is_forbidden(client, make_user):
    owner = make_user(username="owner", api_key="owner-key")
    attacker = make_user(username="attacker", api_key="attacker-key")
    b62 = _b62_id(_upload(client, owner.api_key).get_json())

    # Valid api_key, but not the owner -> 404, file survives.
    resp = client.post("/delete/%s" % b62, data={"k": attacker.api_key})
    assert resp.status_code == 404
    assert File.select().where(File.user == owner).count() == 1


def test_delete_unknown_and_non_b62_id(client, make_user):
    user = make_user()
    assert (
        client.post("/delete/zzzzzz", data={"k": user.api_key}).status_code
        == 404
    )
    assert (
        client.post("/delete/!!!", data={"k": user.api_key}).status_code
        == 404
    )
