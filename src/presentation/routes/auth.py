from sanic import Blueprint, response
from sanic.request import Request

from src.application.dto import LoginRequest, TokenResponse
from src.application.use_cases.auth import GetAdminUseCase, LoginUseCase
from src.presentation.middleware import AuthMiddleware
from src.presentation.utils import require_json


def setup_auth_routes(
    bp: Blueprint,
    login_use_case: LoginUseCase,
    get_admin_use_case: GetAdminUseCase,
    auth_middleware: AuthMiddleware,
) -> None:
    @bp.post("/login")
    async def login(request: Request):
        body = LoginRequest(**require_json(request))
        token, user_id, role = await login_use_case.execute(body.email, body.password)
        return response.json(
            TokenResponse(
                access_token=token,
                user_id=user_id,
                role=role,
            ).model_dump(mode="json")
        )

    @bp.get("/admins/me")
    async def admin_me(request: Request):
        auth_middleware.require_admin(request)
        admin = await get_admin_use_case.execute(request.ctx.user_id)
        return response.json(admin.model_dump(mode="json"))
