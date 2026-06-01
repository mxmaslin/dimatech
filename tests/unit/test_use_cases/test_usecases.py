import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from src.application.errors import (
    AuthenticationError,
    NotFoundError,
    SignatureVerificationError,
)
from src.application.use_cases.auth import LoginUseCase
from src.application.use_cases.payment import ProcessPaymentWebhookUseCase
from src.application.use_cases.user import (
    GetUserUseCase,
    GetUserAccountsUseCase,
    GetUserPaymentsUseCase,
)
from src.application.use_cases.admin import (
    CreateUserUseCase,
    DeleteUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
)
from src.domain.entities import User, Account, Payment
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
            return_value=[
                Account(id=1, user_id=1, balance=Decimal("0.00"))
            ]
        )
        mock_uow.accounts.add_balance = AsyncMock(
            return_value=Account(id=1, user_id=1, balance=Decimal("100.00"))
        )
        mock_uow.payments.create = AsyncMock(
            return_value=Payment(
                transaction_id="tx-1", user_id=1, account_id=1, amount=Decimal("100.00")
            )
        )

        config = MagicMock()
        config.secret_key = "test-secret"

        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        # Compute expected signature: {account_id}{amount}{transaction_id}{user_id}{secret_key}
        raw = f"1{Decimal('100.00')}tx-11test-secret"
        import hashlib
        expected_sig = hashlib.sha256(raw.encode()).hexdigest()

        result = await uc.execute(
            transaction_id="tx-1",
            user_id=1,
            account_id=1,
            amount=Decimal("100.00"),
            signature=expected_sig,
        )

        assert result.transaction_id == "tx-1"
        assert result.amount == Decimal("100.00")

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
