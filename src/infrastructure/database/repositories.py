from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
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
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
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
        result = await self._session.execute(select(AdminModel).where(AdminModel.id == admin_id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[Admin]:
        result = await self._session.execute(select(AdminModel).where(AdminModel.email == email))
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
        stmt = (
            update(AccountModel)
            .where(AccountModel.id == account_id)
            .values(balance=AccountModel.balance + amount)
            .returning(AccountModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        # Account must exist — it was verified/created earlier in the same transaction
        if model is None:
                raise RuntimeError(f"Account {account_id} not found")
        await self._session.flush()
        return self._to_domain(model)

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
            select(PaymentModel).where(PaymentModel.transaction_id == transaction_id)
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

    async def create_if_not_exists(self, payment: Payment) -> tuple[Payment, bool]:
        values = {
            "transaction_id": payment.transaction_id,
            "user_id": payment.user_id,
            "account_id": payment.account_id,
            "amount": payment.amount,
        }
        dialect_name = self._session.get_bind().dialect.name
        if dialect_name == "postgresql":
            insert_fn = pg_insert
        elif dialect_name == "sqlite":
            insert_fn = sqlite_insert
        else:
            raise RuntimeError(f"Unsupported database dialect: {dialect_name}")

        stmt = (
            insert_fn(PaymentModel)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["transaction_id"])
            .returning(PaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        # Note on PostgreSQL version compatibility:
        # PG < 15  → RETURNING returns no row on conflict → model is None
        # PG 15+   → RETURNING may return the existing row (partitioned tables)
        # SQLite   → RETURNING returns no row on conflict → model is None
        # The re-fetch below safely resolves all cases:
        #   - If a row was inserted: model is populated → created=True
        #   - If a conflict occurred: model is None → re-fetch existing → created=False
        if model:
            await self._session.flush()
            return self._to_domain(model), True

        existing = await self.get_by_transaction_id(payment.transaction_id)
        if existing is None:
            raise RuntimeError(f"Payment {payment.transaction_id} conflict without existing row")
        return existing, False

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
