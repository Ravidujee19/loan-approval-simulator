from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    userrole = sa.Enum("admin", "applicant", name="userrole")
    loanstatus = sa.Enum("submitted", "evaluated", "approved", "rejected", "review", name="loanstatus")

    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", userrole, nullable=False, server_default="applicant"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_user_email", "user", ["email"])

    op.create_table(
        "applicant",
        sa.Column("applicant_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE")),
        sa.Column("first_name", sa.String(100)),
        sa.Column("last_name", sa.String(100)),
        sa.Column("email", sa.String(255), unique=True),
        sa.Column("phone", sa.String(30)),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("employment_status", sa.String(50)),
        sa.Column("employer_name", sa.String(255)),
        sa.Column("monthly_income", sa.Numeric(12, 2)),
        sa.Column("other_income", sa.Numeric(12, 2), server_default="0"),
        sa.Column("existing_monthly_debt", sa.Numeric(12, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("ix_applicant_email", "applicant", ["email"])

    op.create_table(
        "evaluation",
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), unique=True),
        sa.Column("eligibility", sa.String(10), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("reasons", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "loanapplication",
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("applicant.applicant_id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("amount_requested", sa.Numeric(12, 2)),
        sa.Column("term_months", sa.Integer()),
        sa.Column("loan_type", sa.String(50)),
        sa.Column("purpose", sa.String(255)),
        sa.Column("application_date", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("status", loanstatus, server_default="submitted"),
        sa.Column(
            "evaluation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation.evaluation_id"),
            unique=True,
            nullable=True,
        ),
        sa.CheckConstraint("amount_requested > 0", name="amount_positive"),
        sa.CheckConstraint("term_months BETWEEN 6 AND 120", name="term_reasonable"),
    )

    op.create_table(
        "agentlog",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("loanapplication.loan_id")),
        sa.Column("agent_name", sa.String(100)),
        sa.Column("message", postgresql.JSONB()),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("config")
    op.drop_table("agentlog")
    op.drop_table("loanapplication")
    op.drop_table("evaluation")
    op.drop_index("ix_applicant_email", table_name="applicant")
    op.drop_table("applicant")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS loanstatus")
