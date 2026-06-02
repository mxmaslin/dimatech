from collections.abc import Callable

from src.application.dto import AccountResponse, PaymentResponse, UserResponse
from src.application.errors import InternalError, NotFoundError
from src.domain.interfaces import UnitOfWork


class GetUserUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self, user_id: int) -> UserResponse:
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User")
            if user.id is None:
                raise InternalError("User id is None after fetch")
            return UserResponse(
                id=user.id,
                email=str(user.email),
                full_name=user.full_name,
            )


class GetUserAccountsUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self, user_id: int) -> list[AccountResponse]:
        async with self._uow_factory() as uow:
            accounts = await uow.accounts.get_by_user_id(user_id)
            result: list[AccountResponse] = []
            for acc in accounts:
                if acc.id is None:
                    raise InternalError("Account id is None after persistence")
                result.append(
                    AccountResponse(
                        id=acc.id,
                        user_id=acc.user_id,
                        balance=acc.balance,
                    )
                )
            return result


class GetUserPaymentsUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def execute(self, user_id: int) -> list[PaymentResponse]:
        async with self._uow_factory() as uow:
            payments = await uow.payments.get_by_user_id(user_id)
            return [
                PaymentResponse(
                    transaction_id=p.transaction_id,
                    user_id=p.user_id,
                    account_id=p.account_id,
                    amount=p.amount,
                    created_at=p.created_at,
                )
                for p in payments
            ]
