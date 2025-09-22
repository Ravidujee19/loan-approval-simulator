# agent audit writing (PII-sanitized)

import structlog
from sqlalchemy.orm import Session

from agents.applicant_evaluator.app.db.models import AgentLog

log = structlog.get_logger()


class AuditLogger:
    @staticmethod
    def log(db: Session, loan_id, agent_name: str, message: dict):
        safe = {k: v for k, v in message.items() if k not in {"email", "phone"}}
        log.info("agent_log", loan_id=str(loan_id), agent=agent_name, **safe)
        db.add(AgentLog(loan_id=loan_id, agent_name=agent_name, message=safe))
        db.commit()
