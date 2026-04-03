"""initial schema

Revision ID: 20260402_0001
Revises:
Create Date: 2026-04-02 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


record_type_enum = sa.Enum("income", "expense", name="recordtype")


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)

    record_type_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "financial_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("type", record_type_enum, nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_financial_records_category"), "financial_records", ["category"], unique=False)
    op.create_index(op.f("ix_financial_records_created_by"), "financial_records", ["created_by"], unique=False)
    op.create_index(op.f("ix_financial_records_date"), "financial_records", ["date"], unique=False)
    op.create_index(op.f("ix_financial_records_id"), "financial_records", ["id"], unique=False)
    op.create_index(op.f("ix_financial_records_type"), "financial_records", ["type"], unique=False)

    op.execute(
        """
        INSERT INTO roles (name, description) VALUES
        ('viewer', 'Can only view dashboard data'),
        ('analyst', 'Can view records and dashboard insights'),
        ('admin', 'Can create update delete records and manage users')
        ON CONFLICT (name) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_records_type"), table_name="financial_records")
    op.drop_index(op.f("ix_financial_records_id"), table_name="financial_records")
    op.drop_index(op.f("ix_financial_records_date"), table_name="financial_records")
    op.drop_index(op.f("ix_financial_records_created_by"), table_name="financial_records")
    op.drop_index(op.f("ix_financial_records_category"), table_name="financial_records")
    op.drop_table("financial_records")

    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")

    record_type_enum.drop(op.get_bind(), checkfirst=True)
