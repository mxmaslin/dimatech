import hashlib
from collections.abc import Callable
from decimal import Decimal

from src.application.dto import PaymentResponse
from src.application.errors import NotFoundError, SignatureVerificationError
from src.domain.entities import Account, Payment
from src.domain.interfaces import SecretKeyProvider, UnitOfWork


def format_amount_for_signature(amount: Decimal) -> str:
    """Canonical amount string for webhook signature (100.00 -> '100')."""
    return format(amount.normalize(), "f")


class ProcessPaymentWebhookUseCase:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        key_provider: SecretKeyProvider,
    ):
        self._uow_factory = uow_factory
        self._key_provider = key_provider

    def _compute_signature(
        self, account_id: int, amount: Decimal, transaction_id: str, user_id: int
    ) -> str:
        raw = (
            f"{account_id}{format_amount_for_signature(amount)}{transaction_id}"
            f"{user_id}{self._key_provider.secret_key}"
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _to_response(payment: Payment) -> PaymentResponse:
        return PaymentResponse(
            transaction_id=payment.transaction_id,
            user_id=payment.user_id,
            account_id=payment.account_id,
            amount=payment.amount,
            created_at=payment.created_at,
        )

    async def execute(
        self,
        transaction_id: str,
        user_id: int,
        account_id: int,
        amount: Decimal,
        signature: str,
    ) -> PaymentResponse:
        expected = self._compute_signature(account_id, amount, transaction_id, user_id)
        if signature != expected:
            raise SignatureVerificationError()

        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise NotFoundError("User")

            existing = await uow.payments.get_by_transaction_id(transaction_id)
            if existing:
                return self._to_response(existing)

            accounts = await uow.accounts.get_by_user_id(user_id)
            account = next((a for a in accounts if a.id == account_id), None)
            if not account:
                account = Account(user_id=user_id, balance=Decimal("0.00"))
                account = await uow.accounts.create(account)
            assert account.id is not None

            payment = Payment(
                transaction_id=transaction_id,
                user_id=user_id,
                account_id=account.id,
                amount=amount,
            )
            payment, created = await uow.payments.create_if_not_exists(payment)
            if not created:
                return self._to_response(payment)

            await uow.accounts.add_balance(account.id, amount)
            return self._to_response(payment)
