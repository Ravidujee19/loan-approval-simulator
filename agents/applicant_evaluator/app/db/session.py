# agents/applicant_evaluator/app/db/session.py
# engine, session, pool config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agents.applicant_evaluator.app.core.config import settings

_engine = create_engine(settings().DATABASE_URL, pool_pre_ping=True, future=True)
_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # migrations via Alembic; nothing here
    pass
