from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.interfaces import (
    AccountRepository,
    AdminRepository,
    PaymentRepository,
    UnitOfWork,
    UserRepository,
)
from src.infrastructure.database.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyAdminRepository,
    SqlAlchemyPaymentRepository,
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = self._session_factory()
        self._users = SqlAlchemyUserRepository(self._session)
        self._admins = SqlAlchemyAdminRepository(self._session)
        self._accounts = SqlAlchemyAccountRepository(self._session)
        self._payments = SqlAlchemyPaymentRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()

    @property
    def users(self) -> UserRepository:
        return self._users

    @property
    def admins(self) -> AdminRepository:
        return self._admins

    @property
    def accounts(self) -> AccountRepository:
        return self._accounts

    @property
    def payments(self) -> PaymentRepository:
        return self._payments
