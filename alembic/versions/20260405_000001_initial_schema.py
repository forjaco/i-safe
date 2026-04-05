"""initial schema

Revision ID: 20260405_000001
Revises:
Create Date: 2026-04-05 00:00:01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "leak_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("encrypted_email", sa.Text(), nullable=False),
        sa.Column("encrypted_report", sa.Text(), nullable=False),
    )
    op.create_index("ix_leak_records_id", "leak_records", ["id"], unique=False)
    op.create_index("ix_leak_records_encrypted_email", "leak_records", ["encrypted_email"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("jti", sa.String(length=64), primary_key=True),
        sa.Column("sub", sa.String(), nullable=False),
        sa.Column("token_type", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parent_jti", sa.String(length=64), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("compromised_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_refresh_tokens_sub", "refresh_tokens", ["sub"], unique=False)
    op.create_index("ix_refresh_tokens_token_type", "refresh_tokens", ["token_type"], unique=False)
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"], unique=False)
    op.create_index("ix_refresh_tokens_parent_jti", "refresh_tokens", ["parent_jti"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_parent_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_type", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_sub", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_leak_records_encrypted_email", table_name="leak_records")
    op.drop_index("ix_leak_records_id", table_name="leak_records")
    op.drop_table("leak_records")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
