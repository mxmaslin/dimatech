from collections.abc import Callable

from src.application.dto import AdminResponse
from src.application.errors import AuthenticationError, InternalError, NotFoundError
from src.domain.interfaces import JwtService, PasswordService, UnitOfWork


class LoginUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        password_service: PasswordService,
        jwt_service: JwtService,
    ):
        self._uow_factory = uow_factory
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def execute(self, email: str, password: str) -> tuple[str, int, str]:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if (
                user
                and user.is_active
                and self._password_service.verify(password, user.password_hash)
            ):
                if user.id is None:
                    raise InternalError("User id is None after fetch")
                token = self._jwt_service.create_access_token(user_id=user.id, role="user")
                return token, user.id, "user"

            admin = await uow.admins.get_by_email(email)
            if admin and self._password_service.verify(password, admin.password_hash):
                if admin.id is None:
                    raise InternalError("Admin id is None after fetch")
                token = self._jwt_service.create_access_token(user_id=admin.id, role="admin")
                return token, admin.id, "admin"

            raise AuthenticationError()


class GetAdminUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self, admin_id: int) -> AdminResponse:
        async with self._uow_factory() as uow:
            admin = await uow.admins.get_by_id(admin_id)
            if not admin:
                raise NotFoundError("Admin")
            if admin.id is None:
                raise InternalError("Admin id is None after fetch")
            return AdminResponse(
                id=admin.id,
                email=str(admin.email),
                full_name=admin.full_name,
            )
