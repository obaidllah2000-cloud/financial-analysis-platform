import os
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from .models import Base, User

DATA_DIR = Path(os.environ.get("FAP_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'platform.db').as_posix()}")
# Hosting providers hand out postgres:// or postgresql:// URLs; use the psycopg 3 driver for both.
for prefix in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(prefix):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(prefix):]

_serverless = bool(os.environ.get("VERCEL"))  # each request may run in a fresh instance: don't hold connections open
engine = create_engine(DATABASE_URL, pool_pre_ping=not _serverless, **({"poolclass": NullPool} if _serverless else {}),
                       connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """Create missing tables and seed default users. On PostgreSQL an advisory lock makes this safe when
    several serverless instances start at the same moment (only one creates tables / seeds at a time)."""
    with engine.begin() as conn:
        if conn.dialect.name == "postgresql":
            conn.execute(text("SELECT pg_advisory_xact_lock(735190421)"))
        Base.metadata.create_all(conn)
        with Session(bind=conn) as s:
            if not s.scalars(select(User)).first():
                s.add_all([User(name="Lead Analyst", role="admin"), User(name="Financial Analyst", role="analyst"),
                           User(name="Reviewer", role="reviewer"), User(name="Management (view only)", role="viewer")])
                s.flush()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
