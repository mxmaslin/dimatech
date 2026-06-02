import uuid
from typing import AsyncGenerator

import bcrypt
import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.infrastructure.config import AppConfig
from src.infrastructure.database.connection import create_engine
from src.infrastructure.database.models import (
    AccountModel,
    AdminModel,
    Base,
    UserModel,
)
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


def _get_session_factory(database_url: str = TEST_DATABASE_URL):
    engine = create_async_engine(database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, factory


async def _seed_test_data(session: AsyncSession) -> None:
    user_pwd = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode()
    admin_pwd = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()

    user = UserModel(
        email="user@example.com",
        password_hash=user_pwd,
        full_name="Test User",
        is_active=True,
    )
    session.add(user)
    await session.flush()

    account = AccountModel(user_id=user.id, balance=0)
    session.add(account)

    admin = AdminModel(
        email="admin@example.com",
        password_hash=admin_pwd,
        full_name="Test Admin",
    )
    session.add(admin)
    await session.commit()


@pytest.fixture(scope="session")
def test_config():
    return AppConfig(
        database_url=TEST_DATABASE_URL,
        secret_key="gfdmhghif38yrf9ew0jkf32",
        jwt_secret="test-jwt-secret-key-that-is-32-bytes!",
        jwt_algorithm="HS256",
        jwt_expiry_minutes=60,
        debug=False,
    )


async def _reset_database(config: AppConfig) -> None:
    """Drop all tables, recreate them, and seed default test data."""
    engine = create_engine(config)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_sessionmaker(engine, class_=AsyncSession)() as session:
        await _seed_test_data(session)

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_sessionmaker(engine, class_=AsyncSession)() as session:
        await _seed_test_data(session)

    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def uow_factory(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    class TestUnitOfWork(SqlAlchemyUnitOfWork):
        pass

    def _factory():
        return TestUnitOfWork(session_factory)

    return _factory


@pytest_asyncio.fixture(scope="function")
async def test_client(test_config):
    """Function-scoped test client with a freshly reset database for isolation."""
    Sanic.test_mode = True
    Sanic._app_registry.clear()

    await _reset_database(test_config)

    from src.main import create_app

    app = create_app(test_config)
    app.name = f"DimaTech-{uuid.uuid4().hex[:8]}"
    yield app.asgi_client
