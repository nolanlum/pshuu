"""Shared pytest fixtures and test isolation.

The application reads configuration at *import time* (``import config`` in
``app.py``; ``from config import ...`` in ``files.py`` / ``api_legacy.py``).
``config.py`` is gitignored, so it is absent in CI and, when present locally,
points at the real ``pshuu.db``/``uploads/``. To stay fully isolated we register
a synthetic ``config`` module in ``sys.modules`` at conftest import time --
*before* pytest collects any test module (and therefore before any
``from files import ...``) -- backed entirely by a throwaway temp directory.
"""

import atexit
import os
import shutil
import sys
import tempfile
import types

import pytest

# Ensure the repo root (containing app.py, db.py, ...) is importable.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# --- Synthetic, isolated config installed before any app module import. ------
TMP_ROOT = tempfile.mkdtemp(prefix="pshuu-test-")
atexit.register(shutil.rmtree, TMP_ROOT, True)

_cfg = types.ModuleType("config")
_cfg.SECRET_KEY = "test-secret"
_cfg.DATABASE = {
    "name": os.path.join(TMP_ROOT, "test.db"),
    "engine": "SqliteDatabase",
}
_cfg.UPLOAD_DIRECTORY = os.path.join(TMP_ROOT, "uploads")
_cfg.THUMBS_DIRECTORY = os.path.join(TMP_ROOT, "thumbs")
_cfg.LEGACY_URL_HOST = "http://localhost"
_cfg.FLASK_PROXY = False
_cfg.DEBUG = False
_cfg.DEBUG_PROFILER = False
_cfg.JSONIFY_PRETTYPRINT_REGULAR = False
sys.modules["config"] = _cfg

# FlaskDB's default before_request handler calls ``connect()`` unconditionally,
# which raises "Connection already opened" whenever a connection is also used
# for direct model access in fixtures/assertions. Make connection handling
# reuse-friendly: one connection per test, opened lazily, closed by the ``db``
# fixture between tests.
from playhouse.flask_utils import FlaskDB  # noqa: E402


def _connect_db(self):
    if self.database.is_closed():
        self.database.connect()


def _close_db(self, exc):
    pass


FlaskDB.connect_db = _connect_db
FlaskDB.close_db = _close_db


@pytest.fixture(scope="session")
def app():
    from app import create

    application = create()
    application.config.update(TESTING=True)
    return application


@pytest.fixture(autouse=True)
def db(app):
    """One DB connection per test; reset tables and close it afterward."""
    from db import database, File, User, ProvisioningKey

    conn = database.database
    if conn.is_closed():
        conn.connect()
    yield database
    # FK order: File references User.
    File.delete().execute()
    User.delete().execute()
    ProvisioningKey.delete().execute()
    if not conn.is_closed():
        conn.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user():
    from db import User

    def _make(username="tester", api_key="test-api-key"):
        return User.create(username=username, api_key=api_key)

    return _make
