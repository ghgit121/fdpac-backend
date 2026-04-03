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
    """Seed default roles into the roles table."""
    roles_table = sa.table(
        'roles',
        sa.column('name', sa.String),
        sa.column('description', sa.String),
    )
    
    op.bulk_insert(
        roles_table,
        [
            {
                'name': 'viewer',
                'description': 'Can only view dashboard data'
            },
            {
                'name': 'analyst',
                'description': 'Can view records and dashboard insights'
            },
            {
                'name': 'admin',
                'description': 'Can manage users and full record CRUD'
            },
        ],
        multiinsert=False,
    )


def downgrade() -> None:
    """Remove seeded roles."""
    op.execute(sa.text("DELETE FROM roles WHERE name IN ('viewer', 'analyst', 'admin')"))
