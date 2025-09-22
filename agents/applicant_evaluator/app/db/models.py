# agents/applicant_evaluator/app/db/models.py
# users, applicants, loan_applications, evaluations...
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    UUID,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agents.applicant_evaluator.app.db.base import Base


class UserRole(enum.Enum):
    admin = "admin"
    applicant = "applicant"


class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.applicant, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    applicants: Mapped[list["Applicant"]] = relationship(back_populates="user")


class Applicant(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        "applicant_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30))
    dob: Mapped[datetime] = mapped_column(Date)

    employment_status: Mapped[str] = mapped_column(String(50))
    employer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    monthly_income: Mapped[float] = mapped_column(Numeric(12, 2))
    other_income: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    existing_monthly_debt: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="applicants")
    loans: Mapped[list["LoanApplication"]] = relationship(back_populates="applicant")


class LoanStatus(enum.Enum):
    submitted = "submitted"
    evaluated = "evaluated"
    approved = "approved"
    rejected = "rejected"
    review = "review"


class LoanApplication(Base):
    id: Mapped[uuid.UUID] = mapped_column("loan_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applicant.applicant_id", ondelete="CASCADE"), index=True
    )
    amount_requested: Mapped[float] = mapped_column(Numeric(12, 2))
    term_months: Mapped[int] = mapped_column(Integer)
    loan_type: Mapped[str] = mapped_column(String(50))
    purpose: Mapped[str] = mapped_column(String(255))
    application_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus), default=LoanStatus.submitted)

    # Optional pointer you already had; NOT used by the relationship below.
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation.evaluation_id"), nullable=True, unique=True
    )

    applicant: Mapped["Applicant"] = relationship(back_populates="loans")

    # ✅ Disambiguated 1–1 relationship via Evaluation.loan_id
    evaluation: Mapped["Evaluation"] = relationship(
        "Evaluation",
        uselist=False,
        primaryjoin="LoanApplication.id == Evaluation.loan_id",
        foreign_keys="[Evaluation.loan_id]",
        back_populates="loan",
    )

    __table_args__ = (
        CheckConstraint("amount_requested > 0", name="amount_positive"),
        CheckConstraint("term_months BETWEEN 6 AND 120", name="term_reasonable"),
    )


class EvaluationOutcome(enum.Enum):
    pass_ = "pass"
    fail = "fail"
    review = "review"


class Evaluation(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        "evaluation_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Unique FK ensures 1–1 with LoanApplication
    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loanapplication.loan_id", ondelete="CASCADE"), unique=True
    )
    eligibility: Mapped[str] = mapped_column(String(10))
    score: Mapped[int] = mapped_column(Integer)
    reasons: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # ✅ Mirror relationship, explicitly tied to loan_id
    loan: Mapped["LoanApplication"] = relationship(
        "LoanApplication",
        primaryjoin="Evaluation.loan_id == LoanApplication.id",
        foreign_keys="[Evaluation.loan_id]",
        back_populates="evaluation",
    )


class AgentLog(Base):
    id: Mapped[uuid.UUID] = mapped_column("log_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loanapplication.loan_id"))
    agent_name: Mapped[str] = mapped_column(String(100))
    message: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Config(Base):
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("key", name="uq_config_key"),)
