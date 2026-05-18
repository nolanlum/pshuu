"""End-to-end: provision a key via manage.py, create a user through the web
flow, upload the real static/pshuu.webm asset, and download it back."""

import os
from urllib.parse import urlsplit

import manage
from db import ProvisioningKey, User

ASSET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
    "pshuu.webm",
)


def test_full_provision_upload_download(client, capsys):
    # 1. Add a provisioning key via manage.py (prints the key to stdout).
    manage.add_provisioning_key()
    key = capsys.readouterr().out.strip()
    assert len(key) == 40
    assert ProvisioningKey.select().where(ProvisioningKey.key == key).count() == 1

    # 2. Create a new user through the real provisioning web flow.
    api_key = "e2e-api-key"
    resp = client.post(
        "/provision/%s" % key,
        data={"username": "e2e-user", "api_key": api_key},
    )
    assert resp.status_code == 302
    assert User.get(User.username == "e2e-user").api_key == api_key
    assert ProvisioningKey.select().where(ProvisioningKey.key == key).count() == 0

    # 3. Upload the real static asset.
    with open(ASSET, "rb") as fh:
        original = fh.read()
    assert len(original) > 0

    up = client.post(
        "/upload",
        data={"k": api_key, "f": (open(ASSET, "rb"), "pshuu.webm")},
        content_type="multipart/form-data",
    )
    assert up.status_code == 200
    share_url = up.get_json()["share_url"]

    # 4. Download it back and verify it is byte-for-byte identical.
    dl = client.get(urlsplit(share_url).path)
    assert dl.status_code == 200
    assert dl.data == original
    assert "pshuu.webm" in dl.headers["Content-Disposition"]
