"""Initial schema: users, admins, accounts, payments + seed data"""
from datetime import datetime
from decimal import Decimal

import bcrypt
from alembic import op
from sqlalchemy import text

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        op.Column("id", op.Integer(), primary_key=True, autoincrement=True),
        op.Column("email", op.String(255), unique=True, nullable=False),
        op.Column("password_hash", op.String(255), nullable=False),
        op.Column("full_name", op.String(255), nullable=False),
        op.Column("is_active", op.Boolean(), server_default=text("true")),
        op.Column(
            "created_at",
            op.DateTime(timezone=True),
            server_default=text("now()"),
        ),
    )

    op.create_table(
        "admins",
        op.Column("id", op.Integer(), primary_key=True, autoincrement=True),
        op.Column("email", op.String(255), unique=True, nullable=False),
        op.Column("password_hash", op.String(255), nullable=False),
        op.Column("full_name", op.String(255), nullable=False),
        op.Column(
            "created_at",
            op.DateTime(timezone=True),
            server_default=text("now()"),
        ),
    )

    op.create_table(
        "accounts",
        op.Column("id", op.Integer(), primary_key=True, autoincrement=True),
        op.Column(
            "user_id",
            op.Integer(),
            op.ForeignKey("users.id"),
            nullable=False,
        ),
        op.Column(
            "balance",
            op.DECIMAL(12, 2),
            nullable=False,
            server_default=text("0.00"),
        ),
        op.Column(
            "created_at",
            op.DateTime(timezone=True),
            server_default=text("now()"),
        ),
    )

    op.create_table(
        "payments",
        op.Column("transaction_id", op.String(255), primary_key=True),
        op.Column(
            "user_id",
            op.Integer(),
            op.ForeignKey("users.id"),
            nullable=False,
        ),
        op.Column(
            "account_id",
            op.Integer(),
            op.ForeignKey("accounts.id"),
            nullable=False,
        ),
        op.Column("amount", op.DECIMAL(12, 2), nullable=False),
        op.Column(
            "created_at",
            op.DateTime(timezone=True),
            server_default=text("now()"),
        ),
    )

    conn = op.get_bind()

    user_password = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode()
    admin_password = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()

    conn.execute(
        text(
            "INSERT INTO users (email, password_hash, full_name) "
            "VALUES (:email, :pwd, :name)"
        ),
        {"email": "user@example.com", "pwd": user_password, "name": "Test User"},
    )

    conn.execute(
        text(
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
        text(
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
