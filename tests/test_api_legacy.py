import io


def _upload_legacy(client, api_key, data=b"legacy", filename="l.txt"):
    return client.post(
        "/api/up",
        data={"k": api_key, "f": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


def test_auth_success_and_failures(client, make_user):
    user = make_user(api_key="legacy-key")

    ok = client.post("/api/auth", data={"e": "tester", "p": "legacy-key"})
    assert ok.data == b"0,legacy-key,,0"

    assert client.post("/api/auth", data={"e": "tester"}).data == b"-1"
    assert (
        client.post("/api/auth", data={"e": "x", "p": "wrong"}).data == b"-1"
    )


def test_legacy_upload_and_download(client, make_user):
    user = make_user(api_key="legacy-key")
    resp = _upload_legacy(client, "legacy-key", b"legacy bytes", "l.txt")
    assert resp.status_code == 200

    fields = resp.data.decode().split(",")
    assert fields[0] == "1"
    share_url = fields[1]
    assert share_url.startswith("http://localhost/")

    path = share_url[len("http://localhost") :]
    dl = client.get(path)
    assert dl.status_code == 200
    assert dl.data == b"legacy bytes"


def test_hist_lists_uploaded_file(client, make_user):
    make_user(api_key="legacy-key")
    _upload_legacy(client, "legacy-key", b"abc", "hist.txt")

    resp = client.post("/api/hist", data={"k": "legacy-key"})
    assert resp.status_code == 200
    text = resp.data.decode()
    assert text.startswith("0\n")
    assert "hist.txt" in text


def test_del_removes_file_and_error_codes(client, make_user):
    make_user(api_key="legacy-key")
    _upload_legacy(client, "legacy-key", b"abc", "del.txt")

    # Non-integer id -> ValueError -> "-1".
    assert (
        client.post(
            "/api/del", data={"k": "legacy-key", "i": "notint"}
        ).data
        == b"-1"
    )
    # Unknown id -> DoesNotExist -> "-2".
    assert (
        client.post(
            "/api/del", data={"k": "legacy-key", "i": "999999"}
        ).data
        == b"-2"
    )

    hist = client.post("/api/hist", data={"k": "legacy-key"}).data.decode()
    file_id = hist.splitlines()[1].split(",")[0]

    deleted = client.post(
        "/api/del", data={"k": "legacy-key", "i": file_id}
    )
    assert deleted.status_code == 200
    assert "del.txt" not in deleted.data.decode()
