# rules engine, scoring, audit logs

from sqlalchemy.orm import Session

from agents.applicant_evaluator.app.core.config import settings
from agents.applicant_evaluator.app.db.models import Evaluation, LoanApplication, LoanStatus
from agents.applicant_evaluator.app.services.config_service import get_rules
from agents.applicant_evaluator.app.services.logs import AuditLogger
from agents.applicant_evaluator.app.services.payments import monthly_payment


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def evaluate_loan(db: Session, loan: LoanApplication) -> Evaluation:
    rules = get_rules(db)
    applicant = loan.applicant
    annual_rate = float(rules.get("ANNUAL_INTEREST_RATE", settings().ANNUAL_INTEREST_RATE))
    min_income = float(rules.get("MIN_INCOME", settings().MIN_INCOME))
    unemployed_min = float(
        rules.get("UNEMPLOYED_MIN_OTHER_INCOME", settings().UNEMPLOYED_MIN_OTHER_INCOME)
    )
    max_debt_ratio = float(rules.get("MAX_DEBT_RATIO", settings().MAX_DEBT_RATIO))

    est_payment = monthly_payment(float(loan.amount_requested), annual_rate, int(loan.term_months))
    debt_ratio = (float(applicant.existing_monthly_debt) + est_payment) / max(
        1.0, float(applicant.monthly_income)
    )

    score = 50
    reasons: list[str] = []
    outcome = "review"

    # Rule 1
    if float(applicant.monthly_income) < min_income and (
        float(loan.amount_requested) / max(1.0, float(applicant.monthly_income)) > 12
    ):
        outcome = "fail"
        reasons.append("Insufficient income vs requested amount")
        score -= 30

    # Rule 2
    if applicant.employment_status == "unemployed" and (
        applicant.other_income is None or float(applicant.other_income) < unemployed_min
    ):
        outcome = "fail"
        reasons.append("Unemployed without sufficient other income")
        score -= 30

    # Rule 3
    if float(applicant.monthly_income) >= min_income and debt_ratio < max_debt_ratio:
        outcome = "pass"
        reasons.append(f"Debt ratio below {int(max_debt_ratio*100)}%")
        reasons.append("Monthly income above threshold")
        score += 20

    if outcome == "review" and not reasons:
        reasons.append("Manual review required")

    score = clamp(score, 0, 100)

    ev = Evaluation(loan_id=loan.id, eligibility=outcome, score=score, reasons=reasons)
    db.add(ev)
    db.commit()
    db.refresh(ev)

    loan.status = (
        LoanStatus.approved if outcome == "pass" else LoanStatus.rejected if outcome == "fail" else LoanStatus.review
    )
    db.add(loan)
    db.commit()

    AuditLogger.log(
        db,
        loan_id=loan.id,
        agent_name="ApplicantEvaluator",
        message={
            "rules": {"annual_rate": annual_rate, "min_income": min_income, "max_debt_ratio": max_debt_ratio},
            "est_payment": est_payment,
            "debt_ratio": debt_ratio,
            "outcome": outcome,
            "score": score,
        },
    )
    return ev
