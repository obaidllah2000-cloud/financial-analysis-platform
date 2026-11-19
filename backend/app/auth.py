"""Shared-password access control for public deployments.

If FAP_PASSWORD is set, every /api route except /api/auth/* needs a signed session cookie obtained by
logging in with that password. If it is not set (local use), the platform stays open.
The password is never stored in code or in the database — only in the server's environment.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

COOKIE = "fap_session"
MAX_AGE = 7 * 24 * 3600
_fallback_secret = secrets.token_hex(32)  # used when FAP_SECRET is unset: sessions end on restart


def password() -> str | None:
    return os.environ.get("FAP_PASSWORD") or None


def _secret() -> bytes:
    return (os.environ.get("FAP_SECRET") or _fallback_secret).encode()


def make_token() -> str:
    ts = str(int(time.time()))
    sig = hmac.new(_secret(), ts.encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"


def valid(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    ts, sig = token.split(".", 1)
    good = hmac.new(_secret(), ts.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, good):
        return False
    try:
        return time.time() - int(ts) < MAX_AGE
    except ValueError:
        return False


def check_password(given: str) -> bool:
    pw = password()
    return bool(pw) and hmac.compare_digest(given.encode(), pw.encode())
