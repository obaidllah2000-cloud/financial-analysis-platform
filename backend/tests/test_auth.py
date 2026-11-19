"""Password gate: off without FAP_PASSWORD, enforced with it."""
import os
import tempfile

os.environ.setdefault("FAP_DATA_DIR", tempfile.mkdtemp())

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_open_without_password(monkeypatch):
    monkeypatch.delenv("FAP_PASSWORD", raising=False)
    with TestClient(app) as c:
        assert c.get("/api/companies").status_code == 200
        assert c.get("/api/auth/status").json() == {"required": False, "logged_in": False}


def test_password_required(monkeypatch):
    monkeypatch.setenv("FAP_PASSWORD", "s3cret-pass")
    monkeypatch.setenv("FAP_SECRET", "test-signing-key")
    with TestClient(app) as c:
        assert c.get("/api/companies").status_code == 401
        assert c.get("/api/template").status_code == 401
        assert c.get("/api/auth/status").json()["required"] is True
        assert c.post("/api/auth/login", json={"password": "wrong"}).status_code == 401
        r = c.post("/api/auth/login", json={"password": "s3cret-pass"})
        assert r.status_code == 200 and "fap_session" in r.cookies
        assert c.get("/api/companies").status_code == 200
        assert c.get("/api/auth/status").json()["logged_in"] is True
        c.post("/api/auth/logout")
        c.cookies.clear()
        assert c.get("/api/companies").status_code == 401
    # a forged cookie is refused
    with TestClient(app) as c:
        c.cookies.set("fap_session", "9999999999.deadbeef")
        assert c.get("/api/companies").status_code == 401
