def test_healthcheck(client):
    resp = client.get("/healthcheck")
    assert resp.status_code == 200
    assert resp.data == b"ok"
    assert resp.mimetype == "text/plain"


def test_index_serves_pshuu_webm(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert len(resp.data) > 0
    assert resp.mimetype == "video/webm"
