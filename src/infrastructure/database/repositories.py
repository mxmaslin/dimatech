from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Account, Admin, Payment, User
from src.domain.value_objects import Email
from src.infrastructure.database.models import (
    AccountModel,
    AdminModel,
    PaymentModel,
    UserModel,
)


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            email=str(user.email),
            password_hash=user.password_hash,
            full_name=user.full_name,
            is_active=user.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def update(self, user: User) -> User:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(
                email=str(user.email),
                password_hash=user.password_hash,
                full_name=user.full_name,
                is_active=user.is_active,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return user

    async def delete(self, user_id: int) -> None:
        await self._session.execute(delete(UserModel).where(UserModel.id == user_id))
        await self._session.flush()

    async def list_all(self) -> list[User]:
        result = await self._session.execute(select(UserModel))
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            password_hash=model.password_hash,
            full_name=model.full_name,
            is_active=model.is_active,
            created_at=model.created_at,
        )


class SqlAlchemyAdminRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, admin_id: int) -> Optional[Admin]:
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.id == admin_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[Admin]:
        result = await self._session.execute(
            select(AdminModel).where(AdminModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, admin: Admin) -> Admin:
        model = AdminModel(
            email=str(admin.email),
            password_hash=admin.password_hash,
            full_name=admin.full_name,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: AdminModel) -> Admin:
        return Admin(
            id=model.id,
            email=Email(model.email),
            password_hash=model.password_hash,
            full_name=model.full_name,
            created_at=model.created_at,
        )


class SqlAlchemyAccountRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.id == account_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_user_id(self, user_id: int) -> list[Account]:
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.user_id == user_id)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def create(self, account: Account) -> Account:
        model = AccountModel(
            user_id=account.user_id,
            balance=account.balance,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def add_balance(self, account_id: int, amount: Decimal) -> Account:
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.id == account_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.balance += amount
            await self._session.flush()
            return self._to_domain(model)
        raise ValueError(f"Account {account_id} not found")

    @staticmethod
    def _to_domain(model: AccountModel) -> Account:
        return Account(
            id=model.id,
            user_id=model.user_id,
            balance=model.balance,
            created_at=model.created_at,
        )


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        result = await self._session.execute(
            select(PaymentModel).where(
                PaymentModel.transaction_id == transaction_id
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, payment: Payment) -> Payment:
        model = PaymentModel(
            transaction_id=payment.transaction_id,
            user_id=payment.user_id,
            account_id=payment.account_id,
            amount=payment.amount,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    async def get_by_user_id(self, user_id: int) -> list[Payment]:
        result = await self._session.execute(
            select(PaymentModel).where(PaymentModel.user_id == user_id)
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: PaymentModel) -> Payment:
        return Payment(
            transaction_id=model.transaction_id,
            user_id=model.user_id,
            account_id=model.account_id,
            amount=model.amount,
            created_at=model.created_at,
        )
