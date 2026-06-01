from decimal import Decimal

from src.application.dto import PaymentResponse
from src.application.errors import NotFoundError, SignatureVerificationError
from src.domain.entities import Account, Payment
from src.domain.interfaces import UnitOfWork
from src.infrastructure.config import AppConfig


class ProcessPaymentWebhookUseCase:
    def __init__(
        self,
        uow_factory: type[UnitOfWork],
        config: AppConfig,
    ):
        self._uow_factory = uow_factory
        self._config = config

    def _compute_signature(
        self, account_id: int, amount: Decimal, transaction_id: str, user_id: int
    ) -> str:
        import hashlib

        raw = f"{account_id}{amount}{transaction_id}{user_id}{self._config.secret_key}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def execute(
        self,
        transaction_id: str,
        user_id: int,
        account_id: int,
        amount: Decimal,
        signature: str,
    ) -> PaymentResponse:
        expected = self._compute_signature(
            account_id, amount, transaction_id, user_id
        )
        if signature != expected:
            raise SignatureVerificationError()

        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User")

            existing = await uow.payments.get_by_transaction_id(transaction_id)
            if existing:
                return PaymentResponse(
                    transaction_id=existing.transaction_id,
                    user_id=existing.user_id,
                    account_id=existing.account_id,
                    amount=existing.amount,
                    created_at=existing.created_at,
                )

            accounts = await uow.accounts.get_by_user_id(user_id)
            account = next((a for a in accounts if a.id == account_id), None)
            if not account:
                account = Account(user_id=user_id, balance=Decimal("0.00"))
                account = await uow.accounts.create(account)
                account_id = account.id  # type: ignore

            await uow.accounts.add_balance(account_id, amount)  # type: ignore
            payment = Payment(
                transaction_id=transaction_id,
                user_id=user_id,
                account_id=account_id,  # type: ignore
                amount=amount,
            )
            payment = await uow.payments.create(payment)

            return PaymentResponse(
                transaction_id=payment.transaction_id,
                user_id=payment.user_id,
                account_id=payment.account_id,
                amount=payment.amount,
                created_at=payment.created_at,
            )
