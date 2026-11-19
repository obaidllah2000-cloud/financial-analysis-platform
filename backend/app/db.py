import os
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from .models import Base, User

DATA_DIR = Path(os.environ.get("FAP_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'platform.db').as_posix()}")
# Hosting providers hand out postgres:// or postgresql:// URLs; use the psycopg 3 driver for both.
for prefix in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(prefix):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(prefix):]

engine = create_engine(DATABASE_URL, pool_pre_ping=True,
                       connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        if not s.scalars(select(User)).first():
            s.add_all([User(name="Lead Analyst", role="admin"), User(name="Financial Analyst", role="analyst"),
                       User(name="Reviewer", role="reviewer"), User(name="Management (view only)", role="viewer")])
            s.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
