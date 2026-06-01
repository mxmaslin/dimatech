from sanic import Blueprint, response
from sanic.request import Request

from src.application.dto import LoginRequest
from src.application.use_cases.auth import GetAdminUseCase, LoginUseCase
from src.presentation.middleware import AuthMiddleware

auth_bp = Blueprint("auth", url_prefix="/auth")


def setup_auth_routes(
    bp: Blueprint,
    login_use_case: LoginUseCase,
    get_admin_use_case: GetAdminUseCase,
    auth_middleware: AuthMiddleware,
) -> None:
    @bp.post("/login")
    async def login(request: Request):
        body = LoginRequest(**request.json)
        token, user_id, role = await login_use_case.execute(body.email, body.password)
        return response.json(
            {
                "access_token": token,
                "token_type": "Bearer",
                "user_id": user_id,
                "role": role,
            }
        )

    @bp.get("/admins/me")
    async def admin_me(request: Request):
        auth_middleware.require_admin(request)
        admin = await get_admin_use_case.execute(request.ctx.user_id)
        return response.json(admin.model_dump(mode="json"))
