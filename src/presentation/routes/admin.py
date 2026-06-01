from sanic import Blueprint, response
from sanic.request import Request

from src.application.dto import UserCreateRequest, UserUpdateRequest
from src.application.use_cases.admin import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserAccountsAdminUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
)
from src.presentation.middleware import AuthMiddleware

admin_bp = Blueprint("admin", url_prefix="/users")


def setup_admin_routes(
    bp: Blueprint,
    create_user_use_case: CreateUserUseCase,
    update_user_use_case: UpdateUserUseCase,
    delete_user_use_case: DeleteUserUseCase,
    list_users_use_case: ListUsersUseCase,
    get_accounts_admin_use_case: GetUserAccountsAdminUseCase,
    auth_middleware: AuthMiddleware,
) -> None:
    @bp.post("/")
    async def create_user(request: Request):
        auth_middleware.require_admin(request)
        body = UserCreateRequest(**request.json)
        user = await create_user_use_case.execute(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
        return response.json(user.model_dump(mode="json"), status=201)

    @bp.get("/")
    async def list_users(request: Request):
        auth_middleware.require_admin(request)
        users = await list_users_use_case.execute()
        return response.json([u.model_dump(mode="json") for u in users])

    @bp.get("/<user_id:int>/accounts")
    async def user_accounts(request: Request, user_id: int):
        auth_middleware.require_admin(request)
        accounts = await get_accounts_admin_use_case.execute(user_id)
        return response.json([a.model_dump(mode="json") for a in accounts])

    @bp.put("/<user_id:int>")
    async def update_user(request: Request, user_id: int):
        auth_middleware.require_admin(request)
        body = UserUpdateRequest(**request.json)
        user = await update_user_use_case.execute(
            user_id=user_id,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
        return response.json(user.model_dump(mode="json"))

    @bp.delete("/<user_id:int>")
    async def delete_user(request: Request, user_id: int):
        auth_middleware.require_admin(request)
        await delete_user_use_case.execute(user_id)
        return response.json({"message": "User deleted"}, status=200)
