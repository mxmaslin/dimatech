from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.use_cases.admin import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserAccountsAdminUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
)
from src.application.use_cases.auth import GetAdminUseCase, LoginUseCase
from src.application.use_cases.payment import ProcessPaymentWebhookUseCase
from src.application.use_cases.user import (
    GetUserAccountsUseCase,
    GetUserPaymentsUseCase,
    GetUserUseCase,
)
from src.domain.interfaces import UnitOfWork
from src.infrastructure.auth.jwt_service import JwtService
from src.infrastructure.auth.password_service import PasswordService
from src.infrastructure.config import AppConfig
from src.infrastructure.database.connection import create_engine, create_session_factory
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class Container:
    def __init__(self, config: AppConfig):
        self._config = config
        self._engine = create_engine(config)
        self._session_factory: async_sessionmaker[AsyncSession] = create_session_factory(
            self._engine
        )
        self._password_service = PasswordService()
        self._jwt_service = JwtService(config)

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    @property
    def password_service(self) -> PasswordService:
        return self._password_service

    @property
    def jwt_service(self) -> JwtService:
        return self._jwt_service

    @property
    def uow_factory(self) -> Callable[[], UnitOfWork]:
        def _factory() -> SqlAlchemyUnitOfWork:
            return SqlAlchemyUnitOfWork(self._session_factory)

        return _factory

    def login_use_case(self) -> LoginUseCase:
        return LoginUseCase(self.uow_factory, self._password_service, self._jwt_service)

    def get_admin_use_case(self) -> GetAdminUseCase:
        return GetAdminUseCase(self.uow_factory)

    def get_user_use_case(self) -> GetUserUseCase:
        return GetUserUseCase(self.uow_factory)

    def get_user_accounts_use_case(self) -> GetUserAccountsUseCase:
        return GetUserAccountsUseCase(self.uow_factory)

    def get_user_payments_use_case(self) -> GetUserPaymentsUseCase:
        return GetUserPaymentsUseCase(self.uow_factory)

    def create_user_use_case(self) -> CreateUserUseCase:
        return CreateUserUseCase(self.uow_factory, self._password_service)

    def update_user_use_case(self) -> UpdateUserUseCase:
        return UpdateUserUseCase(self.uow_factory, self._password_service)

    def delete_user_use_case(self) -> DeleteUserUseCase:
        return DeleteUserUseCase(self.uow_factory)

    def list_users_use_case(self) -> ListUsersUseCase:
        return ListUsersUseCase(self.uow_factory)

    def get_user_accounts_admin_use_case(self) -> GetUserAccountsAdminUseCase:
        return GetUserAccountsAdminUseCase(self.uow_factory)

    def process_payment_use_case(self) -> ProcessPaymentWebhookUseCase:
        return ProcessPaymentWebhookUseCase(self.uow_factory, self._config)
