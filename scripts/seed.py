"""Seed the database with test user and admin accounts.

Usage:
    python scripts/seed.py

Requires DATABASE_URL to be set in the environment (or .env file).
"""

import asyncio
import os

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.config import AppConfig


async def seed() -> None:
    config = AppConfig()
    engine = create_async_engine(config.database_url, echo=config.debug)

    async with engine.begin() as conn:
        user_password = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode()
        admin_password = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()

        await conn.execute(
            text(
                "INSERT INTO users (email, password_hash, full_name) "
                "VALUES (:email, :pwd, :name) "
                "ON CONFLICT (email) DO NOTHING"
            ),
            {"email": "user@example.com", "pwd": user_password, "name": "Test User"},
        )

        await conn.execute(
            text(
                "INSERT INTO admins (email, password_hash, full_name) "
                "VALUES (:email, :pwd, :name) "
                "ON CONFLICT (email) DO NOTHING"
            ),
            {
                "email": "admin@example.com",
                "pwd": admin_password,
                "name": "Test Admin",
            },
        )

        # First user gets the default account
        await conn.execute(
            text(
                "INSERT INTO accounts (user_id, balance) "
                "SELECT id, 0.00 FROM users WHERE email = :email "
                "AND NOT EXISTS (SELECT 1 FROM accounts WHERE user_id = users.id)"
            ),
            {"email": "user@example.com"},
        )

    await engine.dispose()
    print("Seed data inserted successfully.")
    print(f"  User:  user@example.com / user123")
    print(f"  Admin: admin@example.com / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
