import pytest

from db import ProvisioningKey, User


@pytest.fixture
def provisioning_key():
    return ProvisioningKey.create(key="A" * 40)


def test_provision_unknown_key_404(client):
    assert client.get("/provision/doesnotexist").status_code == 404


def test_provision_get_renders_form(client, provisioning_key):
    resp = client.get("/provision/%s" % provisioning_key.key)
    assert resp.status_code == 200


def test_provision_post_creates_user_and_consumes_key(client, provisioning_key):
    resp = client.post(
        "/provision/%s" % provisioning_key.key,
        data={"username": "newbie", "api_key": "newbie-key"},
    )
    assert resp.status_code == 302
    assert "custom_uploader.json" in resp.headers["Location"]

    assert User.get(User.username == "newbie").api_key == "newbie-key"
    assert (
        ProvisioningKey.select()
        .where(ProvisioningKey.key == provisioning_key.key)
        .count()
        == 0
    )


def test_provision_post_duplicate_username(client, provisioning_key, make_user):
    make_user(username="dup", api_key="k1")
    resp = client.post(
        "/provision/%s" % provisioning_key.key,
        data={"username": "dup", "api_key": "k2"},
    )
    assert resp.get_json() == {"error": "duplicate username or API key"}


def test_provision_post_missing_field(client, provisioning_key):
    resp = client.post(
        "/provision/%s" % provisioning_key.key, data={"username": "x"}
    )
    assert resp.get_json() == {"error": "missing required form field"}


def test_provision_sharex_json(client):
    resp = client.get("/provision/some-api-key/custom_uploader.json")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["FileFormName"] == "f"
    assert body["Arguments"]["k"] == "some-api-key"


def test_manage_page_renders(client):
    assert client.get("/manage/some-api-key").status_code == 200
