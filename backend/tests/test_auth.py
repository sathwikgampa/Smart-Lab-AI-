"""Authentication: sign-up, login, sessions, the API login gate, rate limits and password reset."""
from __future__ import annotations

import pytest

from app import create_app
from app.auth.passwords import password_problem
from app.config import TestConfig
from app.db import connect, database_target

GOOD = "Tr1cky-Pipette-42"
ORIGIN = {"Origin": "http://localhost:5173"}


@pytest.fixture()
def auth_app(tmp_path):
    return create_app(TestConfig, DATA_DIR=tmp_path, DATABASE_PATH=tmp_path / "test.db", UPLOAD_DIR=tmp_path / "uploads",
                      INDEX_DIR=tmp_path / "index", AUTH_REQUIRED=True, LOGIN_ATTEMPT_LIMIT=5)


@pytest.fixture()
def web(auth_app):
    return auth_app.test_client()


def signup(client, email="ada@lab.org", password=GOOD, name="Ada Lovelace", **extra):
    body = {"name": name, "email": email, "organization": "Lab 2.14", "password": password, "accepted": True, **extra}
    return client.post("/api/auth/signup", json=body, headers=ORIGIN)


def login(client, email="ada@lab.org", password=GOOD):
    return client.post("/api/auth/login", json={"email": email, "password": password}, headers=ORIGIN)


def cookie(resp):
    return next((h for h in resp.headers.getlist("Set-Cookie") if h.startswith("smartlab_session=")), "")


# ------------------------------------------------------------------ policy
@pytest.mark.parametrize("pw,ok", [
    ("short", False), ("password1234", False), ("PASSWORD1234", False), ("aaaaaaaaaaaaaa", False),
    ("123456789012", False), ("ada.lovelace-2024", False), (GOOD, True), ("correct horse battery", True),
])
def test_password_policy(pw, ok):
    assert (password_problem(pw, "ada.lovelace@lab.org", "Ada Lovelace") is None) is ok


# ------------------------------------------------------------------ gate
def test_api_requires_login_but_health_and_auth_are_public(web):
    assert web.get("/api/health").status_code == 200
    r = web.get("/api/documents")
    assert r.status_code == 401 and r.get_json()["code"] == "auth_required"
    assert web.get("/api/auth/me").get_json()["user"] is None
    # File previews and downloads are behind the same gate.
    assert web.get("/api/documents/1/file").status_code == 401


def test_signup_logs_in_and_unlocks_the_api(web):
    r = signup(web)
    assert r.status_code == 201
    user = r.get_json()["user"]
    assert user["email"] == "ada@lab.org" and user["role"] == "admin" and user["profile_id"]
    assert "password" not in str(user) and "hash" not in str(user)
    set_cookie = cookie(r)
    assert "HttpOnly" in set_cookie and "SameSite=Lax" in set_cookie
    assert web.get("/api/auth/me").get_json()["user"]["name"] == "Ada Lovelace"
    assert web.get("/api/documents").status_code == 200


def test_first_account_is_admin_then_members(auth_app):
    assert signup(auth_app.test_client()).get_json()["user"]["role"] == "admin"
    second = signup(auth_app.test_client(), email="ben@lab.org", name="Ben Ng").get_json()["user"]
    assert second["role"] == "member"


def test_signup_validation(web):
    assert signup(web, password="password1234").get_json()["field"] == "password"
    assert signup(web, password="short").status_code == 400
    assert signup(web, email="not-an-email").get_json()["field"] == "email"
    assert signup(web, accepted=False).get_json()["field"] == "accepted"
    assert signup(web, name="  ").get_json()["field"] == "name"
    assert signup(web).status_code == 201
    dup = signup(web.application.test_client(), email="ADA@lab.org")
    assert dup.status_code == 409 and dup.get_json()["field"] == "email"


def test_passwords_are_hashed_not_stored(auth_app):
    signup(auth_app.test_client())
    conn = connect(database_target(auth_app.config))
    stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    tokens = [r[0] for r in conn.execute("SELECT token_hash FROM auth_sessions")]
    conn.close()
    assert GOOD not in stored and stored.startswith(("scrypt:", "pbkdf2:"))
    assert all(len(t) == 64 for t in tokens)  # SHA-256 hex digests, not the cookie values


def test_login_logout_and_generic_errors(auth_app):
    signup(auth_app.test_client())
    web = auth_app.test_client()
    wrong = login(web, password="Wrong-password-123")
    unknown = login(web, email="nobody@lab.org")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json()["error"] == unknown.get_json()["error"] == "Email or password is incorrect."
    assert login(web, email="ADA@LAB.ORG").status_code == 200  # case-insensitive email
    assert web.get("/api/reagents").status_code == 200
    assert web.post("/api/auth/logout", headers=ORIGIN).status_code == 200
    assert web.get("/api/reagents").status_code == 401


def test_logout_revokes_the_session_server_side(auth_app):
    signup(auth_app.test_client())
    web = auth_app.test_client()
    token = cookie(login(web)).split(";")[0].split("=", 1)[1]
    web.post("/api/auth/logout", headers=ORIGIN)
    replay = auth_app.test_client()
    replay.set_cookie("smartlab_session", token)
    assert replay.get("/api/documents").status_code == 401


def test_login_is_rate_limited(auth_app):
    signup(auth_app.test_client())
    web = auth_app.test_client()
    codes = [login(web, password=f"Wrong-password-{i:03d}").status_code for i in range(7)]
    assert codes[:5] == [401] * 5 and codes[5] == 429
    assert login(web).status_code == 429  # even the right password waits out the window


def test_cross_origin_writes_are_rejected(auth_app):
    web = auth_app.test_client()
    signup(web)
    r = web.post("/api/reagents", json={"name": "x"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_signup_creates_a_profile_used_for_attribution(auth_app):
    web = auth_app.test_client()
    profile_id = signup(web).get_json()["user"]["profile_id"]
    names = {p["id"]: p["name"] for p in web.get("/api/profiles").get_json()}
    assert names[profile_id] == "Ada Lovelace"


# ------------------------------------------------------------------ password reset
def reset_link(auth_app):
    return auth_app.extensions["smartlab_outbox"][-1]["link"]


def test_forgot_password_is_neutral(auth_app):
    signup(auth_app.test_client())
    web = auth_app.test_client()
    known = web.post("/api/auth/forgot-password", json={"email": "ada@lab.org"}, headers=ORIGIN)
    unknown = web.post("/api/auth/forgot-password", json={"email": "nobody@lab.org"}, headers=ORIGIN)
    assert known.status_code == unknown.status_code == 200
    assert known.get_json() == unknown.get_json()
    outbox = auth_app.extensions["smartlab_outbox"]
    assert len(outbox) == 1 and outbox[0]["to"] == "ada@lab.org"
    assert outbox[0]["link"].startswith("http://localhost:5173/#/reset-password?token=")


def test_reset_password_flow(auth_app):
    old_session = auth_app.test_client()
    signup(old_session)
    web = auth_app.test_client()
    web.post("/api/auth/forgot-password", json={"email": "ada@lab.org"}, headers=ORIGIN)
    token = reset_link(auth_app).split("token=", 1)[1]

    weak = web.post("/api/auth/reset-password", json={"token": token, "password": "password1234"}, headers=ORIGIN)
    assert weak.status_code == 400 and weak.get_json()["field"] == "password"
    new = "Another-Long-Secret-7"
    assert web.post("/api/auth/reset-password", json={"token": token, "password": new}, headers=ORIGIN).status_code == 200
    # Single use; existing sessions are signed out; only the new password works.
    again = web.post("/api/auth/reset-password", json={"token": token, "password": "Yet-Another-Secret-8"}, headers=ORIGIN)
    assert again.status_code == 400
    assert old_session.get("/api/documents").status_code == 401
    assert login(auth_app.test_client()).status_code == 401
    assert login(auth_app.test_client(), password=new).status_code == 200


def test_reset_token_expires_and_only_newest_works(auth_app):
    signup(auth_app.test_client())
    web = auth_app.test_client()
    web.post("/api/auth/forgot-password", json={"email": "ada@lab.org"}, headers=ORIGIN)
    first = reset_link(auth_app).split("token=", 1)[1]
    web.post("/api/auth/forgot-password", json={"email": "ada@lab.org"}, headers=ORIGIN)
    second = reset_link(auth_app).split("token=", 1)[1]
    assert web.post("/api/auth/reset-password", json={"token": first, "password": "Another-Long-Secret-7"}, headers=ORIGIN).status_code == 400

    conn = connect(database_target(auth_app.config))
    conn.execute("UPDATE password_resets SET expires_at = '2000-01-01 00:00:00'")
    conn.commit()
    conn.close()
    assert web.post("/api/auth/reset-password", json={"token": second, "password": "Another-Long-Secret-7"}, headers=ORIGIN).status_code == 400
    assert web.post("/api/auth/reset-password", json={"token": "made-up", "password": "Another-Long-Secret-7"}, headers=ORIGIN).status_code == 400
