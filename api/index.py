"""Vercel entry point: runs the FastAPI app as a serverless function.

Vercel's file system is read-only except /tmp, and it does not run FastAPI's startup (lifespan) hook,
so the data folder points at /tmp and the tables are created when the function first loads.
"""
import os
import sys

os.environ.setdefault("FAP_DATA_DIR", "/tmp/fap-data")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402,F401  (Vercel serves the ASGI object named `app`)

try:
    init_db()  # idempotent: creates missing tables and the default users
except Exception as exc:  # keep the function alive so /api/auth/status can still answer
    print(f"init_db failed: {exc}")
