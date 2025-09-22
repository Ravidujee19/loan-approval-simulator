# create admin, configs, sample applicants

from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.applicant_evaluator.app.core.config import settings
from agents.applicant_evaluator.app.db.session import _SessionLocal
from agents.applicant_evaluator.app.db.models import User, UserRole, Applicant, Config
from agents.applicant_evaluator.app.utils.crypto import get_password_hash
import json
from pathlib import Path


def run_seed() -> None:
    db: Session = _SessionLocal()
    try:
        # admin
        if not db.scalar(select(User).where(User.email == settings().DEFAULT_ADMIN_EMAIL)):
            admin = User(
                email=settings().DEFAULT_ADMIN_EMAIL,
                password_hash=get_password_hash(settings().DEFAULT_ADMIN_PASSWORD),
                role=UserRole.admin,
            )
            db.add(admin)
            db.commit()

        # rules config
        if not db.get(Config, "rules"):
            db.add(
                Config(
                    key="rules",
                    value={
                        "MIN_INCOME": settings().MIN_INCOME,
                        "UNEMPLOYED_MIN_OTHER_INCOME": settings().UNEMPLOYED_MIN_OTHER_INCOME,
                        "MAX_DEBT_RATIO": settings().MAX_DEBT_RATIO,
                        "ANNUAL_INTEREST_RATE": settings().ANNUAL_INTEREST_RATE,
                    },
                )
            )
            db.commit()

        # sample applicants
        sample_file = Path("data/samples/applicants.json")
        if sample_file.exists():
            data = json.loads(sample_file.read_text())
            for row in data:
                if not db.scalar(select(User).where(User.email == row["email"])):
                    user = User(email=row["email"], password_hash=get_password_hash("User@12345"))
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    db.add(Applicant(user_id=user.id, **row))
                    db.commit()
    finally:
        db.close()
