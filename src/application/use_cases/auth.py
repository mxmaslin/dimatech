from src.application.dto import AdminResponse
from src.application.errors import AuthenticationError, NotFoundError
from src.domain.interfaces import UnitOfWork
from src.infrastructure.auth.jwt_service import JwtService
from src.infrastructure.auth.password_service import PasswordService


class LoginUseCase:
    def __init__(
        self,
        uow_factory: type[UnitOfWork],
        password_service: PasswordService,
        jwt_service: JwtService,
    ):
        self._uow_factory = uow_factory
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def execute(
        self, email: str, password: str
    ) -> tuple[str, int, str]:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            if user and self._password_service.verify(password, user.password_hash):
                token = self._jwt_service.create_access_token(
                    user_id=user.id, role="user"  # type: ignore
                )
                return token, user.id, "user"  # type: ignore

            admin = await uow.admins.get_by_email(email)
            if admin and self._password_service.verify(
                password, admin.password_hash
            ):
                token = self._jwt_service.create_access_token(
                    user_id=admin.id, role="admin"  # type: ignore
                )
                return token, admin.id, "admin"  # type: ignore

            raise AuthenticationError()


class GetAdminUseCase:
    def __init__(self, uow_factory: type[UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self, admin_id: int) -> AdminResponse:
        async with self._uow_factory() as uow:
            admin = await uow.admins.get_by_id(admin_id)
            if not admin:
                raise NotFoundError("Admin")
            return AdminResponse(
                id=admin.id,  # type: ignore
                email=str(admin.email),
                full_name=admin.full_name,
            )
