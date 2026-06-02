from collections.abc import Callable

from src.application.dto import AccountResponse, UserResponse
from src.application.errors import DuplicateError, NotFoundError
from src.domain.entities import User
from src.domain.interfaces import PasswordService, UnitOfWork
from src.domain.value_objects import Email


class CreateUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        password_service: PasswordService,
    ):
        self._uow_factory = uow_factory
        self._password_service = password_service

    async def execute(self, email: str, password: str, full_name: str) -> UserResponse:
        async with self._uow_factory() as uow:
            existing = await uow.users.get_by_email(email)
            if existing:
                raise DuplicateError("User with this email already exists")

            password_hash = self._password_service.hash(password)
            user = User(
                email=Email(email),
                password_hash=password_hash,
                full_name=full_name,
            )
            user = await uow.users.create(user)
            if user.id is None:
                raise RuntimeError("CreateUserUseCase: user.id is None after create")
            return UserResponse(
                id=user.id,
                email=str(user.email),
                full_name=user.full_name,
            )


class UpdateUserUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        password_service: PasswordService,
    ):
        self._uow_factory = uow_factory
        self._password_service = password_service

    async def execute(
        self,
        user_id: int,
        email: str | None = None,
        password: str | None = None,
        full_name: str | None = None,
    ) -> UserResponse:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User")

            if email and email != str(user.email):
                existing = await uow.users.get_by_email(email)
                if existing:
                    raise DuplicateError("User with this email already exists")
                user.email = Email(email)
            if password:
                user.password_hash = self._password_service.hash(password)
            if full_name:
                user.full_name = full_name

            user = await uow.users.update(user)
            if user.id is None:
                raise RuntimeError("UpdateUserUseCase: user.id is None after update")
            return UserResponse(
                id=user.id,
                email=str(user.email),
                full_name=user.full_name,
            )


class DeleteUserUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self, user_id: int) -> None:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User")
            await uow.users.delete(user_id)


class ListUsersUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self) -> list[UserResponse]:
        async with self._uow_factory() as uow:
            users = await uow.users.list_all()
            return [
                UserResponse(
                    id=u.id,  # type: ignore[arg-type]
                    email=str(u.email),
                    full_name=u.full_name,
                )
                for u in users
            ]


class GetUserAccountsAdminUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self, user_id: int) -> list[AccountResponse]:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User")
            accounts = await uow.accounts.get_by_user_id(user_id)
            return [
                AccountResponse(
                    id=acc.id,  # type: ignore[arg-type]
                    user_id=acc.user_id,
                    balance=acc.balance,
                )
                for acc in accounts
            ]
