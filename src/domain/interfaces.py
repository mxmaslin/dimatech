import sys
from abc import ABC, abstractmethod
from decimal import Decimal
from types import TracebackType
from typing import Any, Optional, Protocol

from src.domain.entities import Account, Admin, Payment, User


class PasswordService(Protocol):
    """Domain protocol for password hashing and verification."""

    def hash(self, plain_password: str) -> str: ...
    def verify(self, plain_password: str, hashed: str) -> bool: ...


class JwtService(Protocol):
    """Domain protocol for JWT token creation and decoding."""

    def create_access_token(self, user_id: int, role: str) -> str: ...
    def decode_token(self, token: str) -> dict[str, Any]: ...


class SecretKeyProvider(Protocol):
    """Domain protocol for accessing the secret key used in signatures."""

    @property
    def secret_key(self) -> str: ...


class UserRepository(Protocol):
    async def get_by_id(self, user_id: int) -> Optional[User]: ...

    async def get_by_email(self, email: str) -> Optional[User]: ...

    async def create(self, user: User) -> User: ...

    async def update(self, user: User) -> User: ...

    async def delete(self, user_id: int) -> None: ...

    async def list_all(self) -> list[User]: ...


class AdminRepository(Protocol):
    async def get_by_id(self, admin_id: int) -> Optional[Admin]: ...

    async def get_by_email(self, email: str) -> Optional[Admin]: ...

    async def create(self, admin: Admin) -> Admin: ...


class AccountRepository(Protocol):
    async def get_by_id(self, account_id: int) -> Optional[Account]: ...

    async def get_by_user_id(self, user_id: int) -> list[Account]: ...

    async def create(self, account: Account) -> Account: ...

    async def add_balance(self, account_id: int, amount: Decimal) -> Account: ...


class PaymentRepository(Protocol):
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]: ...

    async def create(self, payment: Payment) -> Payment: ...

    async def create_if_not_exists(self, payment: Payment) -> tuple[Payment, bool]: ...

    async def get_by_user_id(self, user_id: int) -> list[Payment]: ...


class UnitOfWork(ABC):
    @abstractmethod
    async def __aenter__(self): ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    @property
    @abstractmethod
    def users(self) -> UserRepository: ...

    @property
    @abstractmethod
    def admins(self) -> AdminRepository: ...

    @property
    @abstractmethod
    def accounts(self) -> AccountRepository: ...

    @property
    @abstractmethod
    def payments(self) -> PaymentRepository: ...
