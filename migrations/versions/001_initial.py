"""Initial schema: users, admins, accounts, payments + seed data"""
from datetime import datetime
from decimal import Decimal

import bcrypt
import sqlalchemy as sa
from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "balance",
            sa.DECIMAL(12, 2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "payments",
        sa.Column("transaction_id", sa.String(255), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.DECIMAL(12, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    conn = op.get_bind()

    user_password = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode()
    admin_password = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()

    conn.execute(
        sa.text(
            "INSERT INTO users (email, password_hash, full_name) "
            "VALUES (:email, :pwd, :name)"
        ),
        {"email": "user@example.com", "pwd": user_password, "name": "Test User"},
    )

    conn.execute(
        sa.text(
            "INSERT INTO admins (email, password_hash, full_name) "
            "VALUES (:email, :pwd, :name)"
        ),
        {
            "email": "admin@example.com",
            "pwd": admin_password,
            "name": "Test Admin",
        },
    )

    conn.execute(
        sa.text(
            "INSERT INTO accounts (user_id, balance) "
            "VALUES (:uid, :bal)"
        ),
        {"uid": 1, "bal": Decimal("0.00")},
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("accounts")
    op.drop_table("admins")
    op.drop_table("users")
