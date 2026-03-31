"""Enable RLS on rulesets.

Revision ID: 20260401_0004
Revises: 20260309_0003
Create Date: 2026-04-01 12:00:00
"""

from alembic import op


revision = "20260401_0004"
down_revision = "20260309_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.rulesets ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE public.rulesets DISABLE ROW LEVEL SECURITY")
