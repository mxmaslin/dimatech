from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.config import AppConfig


def create_engine(config: AppConfig):
    return create_async_engine(
        config.database_url,
        echo=config.debug,
        pool_size=config.db_pool_size,
        max_overflow=config.db_max_overflow,
    )


def create_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
