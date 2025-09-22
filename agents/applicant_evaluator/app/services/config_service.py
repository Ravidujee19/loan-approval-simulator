# thresholds storage/retrieval (Config table)

from sqlalchemy.orm import Session

from agents.applicant_evaluator.app.core.config import settings
from agents.applicant_evaluator.app.db.models import Config


def get_rules(db: Session) -> dict:
    cfg = db.get(Config, "rules")
    if cfg:
        return cfg.value
    # env defaults
    return {
        "ANNUAL_INTEREST_RATE": settings().ANNUAL_INTEREST_RATE,
        "MIN_INCOME": settings().MIN_INCOME,
        "UNEMPLOYED_MIN_OTHER_INCOME": settings().UNEMPLOYED_MIN_OTHER_INCOME,
        "MAX_DEBT_RATIO": settings().MAX_DEBT_RATIO,
    }
