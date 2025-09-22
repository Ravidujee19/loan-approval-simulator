# from alembic import op
# import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql

# revision = "0002_config_defaults"
# down_revision = "0001_init"
# branch_labels = None
# depends_on = None


# def upgrade() -> None:
#     op.execute(
#         """
#         INSERT INTO config(key, value) VALUES
#         ('rules', '{"MIN_INCOME":50000,"UNEMPLOYED_MIN_OTHER_INCOME":25000,"MAX_DEBT_RATIO":0.4,"ANNUAL_INTEREST_RATE":0.12}')
#         ON CONFLICT (key) DO NOTHING
#         """
#     )


# def downgrade() -> None:
#     op.execute("DELETE FROM config WHERE key='rules'")

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_config_defaults"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert default rule config as JSONB
    op.execute("""
        INSERT INTO config (key, value)
        VALUES (
            'rules',
            '{"MIN_INCOME": 50000, "UNEMPLOYED_MIN_OTHER_INCOME": 25000, "MAX_DEBT_RATIO": 0.4, "ANNUAL_INTEREST_RATE": 0.12}'::jsonb
        )
        ON CONFLICT (key) DO NOTHING;
    """)


def downgrade() -> None:
    # Remove only if the value matches the defaults inserted in upgrade()
    op.execute("""
        DELETE FROM config
        WHERE key = 'rules'
        AND value = '{"MIN_INCOME": 50000, "UNEMPLOYED_MIN_OTHER_INCOME": 25000, "MAX_DEBT_RATIO": 0.4, "ANNUAL_INTEREST_RATE": 0.12}'::jsonb;
    """)
