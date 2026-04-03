"""Seed default roles.

Revision ID: 20260403_0002
Revises: 20260402_0001
Create Date: 2026-04-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260403_0002'
down_revision = '20260402_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ensure default roles exist (idempotent — safe to run on any database state)."""
    # Migration 0001 already seeds these roles, but may not have run on older
    # databases.  Using ON CONFLICT DO NOTHING makes this migration safe to apply
    # regardless of whether the rows already exist.
    op.execute(sa.text("""
        INSERT INTO roles (name, description) VALUES
        ('viewer',  'Can only view dashboard data'),
        ('analyst', 'Can view records and dashboard insights'),
        ('admin',   'Can manage users and full record CRUD')
        ON CONFLICT (name) DO NOTHING;
    """))


def downgrade() -> None:
    """Remove seeded roles."""
    op.execute(sa.text("DELETE FROM roles WHERE name IN ('viewer', 'analyst', 'admin')"))
