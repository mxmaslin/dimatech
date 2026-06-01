import hashlib
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.errors import AuthenticationError, SignatureVerificationError
from src.application.use_cases.auth import LoginUseCase
from src.application.use_cases.payment import (
    ProcessPaymentWebhookUseCase,
    format_amount_for_signature,
)
from src.domain.entities import Account, Payment, User
from src.domain.value_objects import Email


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None
    return uow


@pytest.fixture
def mock_uow_factory(mock_uow):
    return MagicMock(return_value=mock_uow)


class TestLoginUseCase:
    @pytest.mark.asyncio
    async def test_user_login_success(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_email = AsyncMock(
            return_value=User(
                id=1,
                email=Email("user@example.com"),
                password_hash="$2b$12$hashedpassword",
                full_name="Test User",
            )
        )
        mock_uow.admins.get_by_email = AsyncMock(return_value=None)

        password_service = MagicMock()
        password_service.verify = MagicMock(return_value=True)

        jwt_service = MagicMock()
        jwt_service.create_access_token = MagicMock(return_value="test-token")

        uc = LoginUseCase(mock_uow_factory, password_service, jwt_service)
        token, uid, role = await uc.execute("user@example.com", "password")

        assert token == "test-token"
        assert uid == 1
        assert role == "user"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_email = AsyncMock(return_value=None)
        mock_uow.admins.get_by_email = AsyncMock(return_value=None)

        password_service = MagicMock()
        jwt_service = MagicMock()
        uc = LoginUseCase(mock_uow_factory, password_service, jwt_service)

        with pytest.raises(AuthenticationError):
            await uc.execute("bad@email.com", "wrong")


class TestProcessPaymentWebhookUseCase:
    @pytest.mark.asyncio
    async def test_valid_webhook_creates_payment(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(
            return_value=User(
                id=1, email=Email("user@test.com"), password_hash="x", full_name="Test"
            )
        )
        mock_uow.payments.get_by_transaction_id = AsyncMock(return_value=None)
        mock_uow.accounts.get_by_user_id = AsyncMock(
            return_value=[Account(id=1, user_id=1, balance=Decimal("0.00"))]
        )
        mock_uow.accounts.add_balance = AsyncMock(
            return_value=Account(id=1, user_id=1, balance=Decimal("100.00"))
        )
        mock_uow.payments.create_if_not_exists = AsyncMock(
            return_value=(
                Payment(
                    transaction_id="tx-1",
                    user_id=1,
                    account_id=1,
                    amount=Decimal("100.00"),
                ),
                True,
            )
        )

        config = MagicMock()
        config.secret_key = "test-secret"

        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        amount = Decimal("100.00")
        raw = f"1{format_amount_for_signature(amount)}tx-11{config.secret_key}"
        expected_sig = hashlib.sha256(raw.encode()).hexdigest()

        result = await uc.execute(
            transaction_id="tx-1",
            user_id=1,
            account_id=1,
            amount=amount,
            signature=expected_sig,
        )

        assert result.transaction_id == "tx-1"
        assert result.amount == Decimal("100.00")
        mock_uow.accounts.add_balance.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_duplicate_webhook_skips_balance_credit(self, mock_uow, mock_uow_factory):
        existing_payment = Payment(
            transaction_id="tx-1",
            user_id=1,
            account_id=1,
            amount=Decimal("100.00"),
        )
        mock_uow.users.get_by_id = AsyncMock(
            return_value=User(
                id=1, email=Email("user@test.com"), password_hash="x", full_name="Test"
            )
        )
        mock_uow.payments.get_by_transaction_id = AsyncMock(return_value=None)
        mock_uow.accounts.get_by_user_id = AsyncMock(
            return_value=[Account(id=1, user_id=1, balance=Decimal("100.00"))]
        )
        mock_uow.payments.create_if_not_exists = AsyncMock(return_value=(existing_payment, False))

        config = MagicMock()
        config.secret_key = "test-secret"
        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        amount = Decimal("100.00")
        raw = f"1{format_amount_for_signature(amount)}tx-11{config.secret_key}"
        expected_sig = hashlib.sha256(raw.encode()).hexdigest()

        result = await uc.execute(
            transaction_id="tx-1",
            user_id=1,
            account_id=1,
            amount=amount,
            signature=expected_sig,
        )

        assert result.transaction_id == "tx-1"
        mock_uow.accounts.add_balance.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_spec_example_signature(self, mock_uow_factory):
        config = MagicMock()
        config.secret_key = "gfdmhghif38yrf9ew0jkf32"
        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        signature = uc._compute_signature(
            account_id=1,
            amount=Decimal("100"),
            transaction_id="5eae174f-7cd0-472c-bd36-35660f00132b",
            user_id=1,
        )
        assert signature == "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"

    @pytest.mark.asyncio
    async def test_amount_normalization_in_signature(self, mock_uow_factory):
        config = MagicMock()
        config.secret_key = "test-secret"
        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        sig_int = uc._compute_signature(1, Decimal("100"), "tx-1", 1)
        sig_decimal = uc._compute_signature(1, Decimal("100.00"), "tx-1", 1)
        sig_float_parsed = uc._compute_signature(1, Decimal("100.0"), "tx-1", 1)

        assert sig_int == sig_decimal == sig_float_parsed

    @pytest.mark.asyncio
    async def test_invalid_signature(self, mock_uow_factory):
        config = MagicMock()
        config.secret_key = "test-secret"

        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        with pytest.raises(SignatureVerificationError):
            await uc.execute(
                transaction_id="tx-1",
                user_id=1,
                account_id=1,
                amount=Decimal("100.00"),
                signature="invalid-signature",
            )
