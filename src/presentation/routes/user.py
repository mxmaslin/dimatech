from sanic import Blueprint, response
from sanic.request import Request

from src.application.use_cases.user import (
    GetUserAccountsUseCase,
    GetUserPaymentsUseCase,
    GetUserUseCase,
)
from src.presentation.middleware import AuthMiddleware

def setup_user_routes(
    bp: Blueprint,
    get_user_use_case: GetUserUseCase,
    get_accounts_use_case: GetUserAccountsUseCase,
    get_payments_use_case: GetUserPaymentsUseCase,
    auth_middleware: AuthMiddleware,
) -> None:
    @bp.get("/me")
    async def me(request: Request):
        auth_middleware.require_user(request)
        user = await get_user_use_case.execute(request.ctx.user_id)
        return response.json(user.model_dump(mode="json"))

    @bp.get("/me/accounts")
    async def my_accounts(request: Request):
        auth_middleware.require_user(request)
        accounts = await get_accounts_use_case.execute(request.ctx.user_id)
        return response.json([a.model_dump(mode="json") for a in accounts])

    @bp.get("/me/payments")
    async def my_payments(request: Request):
        auth_middleware.require_user(request)
        payments = await get_payments_use_case.execute(request.ctx.user_id)
        return response.json([p.model_dump(mode="json") for p in payments])
