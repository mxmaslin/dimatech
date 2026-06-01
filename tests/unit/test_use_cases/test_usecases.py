import hashlib
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.errors import (
    AuthenticationError,
    DuplicateError,
    NotFoundError,
    SignatureVerificationError,
)
from src.application.use_cases.admin import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserAccountsAdminUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
)
from src.application.use_cases.auth import GetAdminUseCase, LoginUseCase
from src.application.use_cases.payment import (
    ProcessPaymentWebhookUseCase,
    format_amount_for_signature,
)
from src.application.use_cases.user import (
    GetUserAccountsUseCase,
    GetUserPaymentsUseCase,
    GetUserUseCase,
)
from src.domain.entities import Account, Admin, Payment, User
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


@pytest.fixture
def password_service():
    svc = MagicMock()
    svc.hash = MagicMock(return_value="$2b$12$hashedpassword")
    svc.verify = MagicMock(return_value=True)
    return svc


@pytest.fixture
def jwt_service():
    svc = MagicMock()
    svc.create_access_token = MagicMock(return_value="test-token")
    svc.decode_token = MagicMock(return_value={"user_id": 1, "role": "user"})
    return svc


class TestLoginUseCase:
    @pytest.mark.asyncio
    async def test_user_login_success(
        self, mock_uow, mock_uow_factory, password_service, jwt_service
    ):
        mock_uow.users.get_by_email = AsyncMock(
            return_value=User(
                id=1,
                email=Email("user@example.com"),
                password_hash="$2b$12$hashedpassword",
                full_name="Test User",
            )
        )
        mock_uow.admins.get_by_email = AsyncMock(return_value=None)

        uc = LoginUseCase(mock_uow_factory, password_service, jwt_service)
        token, uid, role = await uc.execute("user@example.com", "password")

        assert token == "test-token"
        assert uid == 1
        assert role == "user"

    @pytest.mark.asyncio
    async def test_admin_login_success(
        self, mock_uow, mock_uow_factory, password_service, jwt_service
    ):
        mock_uow.users.get_by_email = AsyncMock(return_value=None)
        mock_uow.admins.get_by_email = AsyncMock(
            return_value=Admin(
                id=2,
                email=Email("admin@example.com"),
                password_hash="$2b$12$hashed",
                full_name="Test Admin",
            )
        )

        uc = LoginUseCase(mock_uow_factory, password_service, jwt_service)
        token, uid, role = await uc.execute("admin@example.com", "password")

        assert token == "test-token"
        assert uid == 2
        assert role == "admin"

    @pytest.mark.asyncio
    async def test_login_inactive_user_fails(
        self, mock_uow, mock_uow_factory, password_service, jwt_service
    ):
        mock_uow.users.get_by_email = AsyncMock(
            return_value=User(
                id=1,
                email=Email("inactive@test.com"),
                password_hash="$2b$12$hash",
                full_name="Inactive User",
                is_active=False,
            )
        )
        mock_uow.admins.get_by_email = AsyncMock(return_value=None)

        uc = LoginUseCase(mock_uow_factory, password_service, jwt_service)
        with pytest.raises(AuthenticationError):
            await uc.execute("inactive@test.com", "password")

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_email = AsyncMock(return_value=None)
        mock_uow.admins.get_by_email = AsyncMock(return_value=None)

        password_service = MagicMock()
        jwt_service = MagicMock()
        uc = LoginUseCase(mock_uow_factory, password_service, jwt_service)

        with pytest.raises(AuthenticationError):
            await uc.execute("bad@email.com", "wrong")


class TestGetAdminUseCase:
    @pytest.mark.asyncio
    async def test_admin_found(self, mock_uow, mock_uow_factory):
        mock_uow.admins.get_by_id = AsyncMock(
            return_value=Admin(
                id=1, email=Email("admin@test.com"), password_hash="hash", full_name="Admin Name"
            )
        )
        uc = GetAdminUseCase(mock_uow_factory)
        result = await uc.execute(1)
        assert result.id == 1
        assert result.email == "admin@test.com"
        assert result.full_name == "Admin Name"

    @pytest.mark.asyncio
    async def test_admin_not_found(self, mock_uow, mock_uow_factory):
        mock_uow.admins.get_by_id = AsyncMock(return_value=None)
        uc = GetAdminUseCase(mock_uow_factory)
        with pytest.raises(NotFoundError):
            await uc.execute(999)


class TestGetUserUseCase:
    @pytest.mark.asyncio
    async def test_user_found(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(
            return_value=User(
                id=1, email=Email("user@test.com"), password_hash="hash", full_name="User Name"
            )
        )
        uc = GetUserUseCase(mock_uow_factory)
        result = await uc.execute(1)
        assert result.id == 1
        assert result.email == "user@test.com"

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(return_value=None)
        uc = GetUserUseCase(mock_uow_factory)
        with pytest.raises(NotFoundError):
            await uc.execute(999)


class TestGetUserAccountsUseCase:
    @pytest.mark.asyncio
    async def test_returns_accounts(self, mock_uow, mock_uow_factory):
        mock_uow.accounts.get_by_user_id = AsyncMock(
            return_value=[Account(id=1, user_id=1, balance=Decimal("50.00"))]
        )
        uc = GetUserAccountsUseCase(mock_uow_factory)
        result = await uc.execute(1)
        assert len(result) == 1
        assert result[0].balance == Decimal("50.00")


class TestGetUserPaymentsUseCase:
    @pytest.mark.asyncio
    async def test_returns_payments(self, mock_uow, mock_uow_factory):
        mock_uow.payments.get_by_user_id = AsyncMock(
            return_value=[
                Payment(transaction_id="tx-1", user_id=1, account_id=1, amount=Decimal("100.00"))
            ]
        )
        uc = GetUserPaymentsUseCase(mock_uow_factory)
        result = await uc.execute(1)
        assert len(result) == 1
        assert result[0].transaction_id == "tx-1"


class TestCreateUserUseCase:
    @pytest.mark.asyncio
    async def test_creates_user(self, mock_uow, mock_uow_factory, password_service):
        mock_uow.users.get_by_email = AsyncMock(return_value=None)
        mock_uow.users.create = AsyncMock(
            return_value=User(
                id=1, email=Email("new@test.com"), password_hash="hash", full_name="New User"
            )
        )
        uc = CreateUserUseCase(mock_uow_factory, password_service)
        result = await uc.execute("new@test.com", "secure123", "New User")
        assert result.id == 1
        assert result.email == "new@test.com"

    @pytest.mark.asyncio
    async def test_duplicate_email_raises(self, mock_uow, mock_uow_factory, password_service):
        mock_uow.users.get_by_email = AsyncMock(
            return_value=User(
                email=Email("existing@test.com"), password_hash="hash", full_name="Existing"
            )
        )
        uc = CreateUserUseCase(mock_uow_factory, password_service)
        with pytest.raises(DuplicateError):
            await uc.execute("existing@test.com", "pass", "Existing")


class TestUpdateUserUseCase:
    @pytest.mark.asyncio
    async def test_updates_email(self, mock_uow, mock_uow_factory, password_service):
        existing = User(id=1, email=Email("old@test.com"), password_hash="hash", full_name="User")
        mock_uow.users.get_by_id = AsyncMock(return_value=existing)
        mock_uow.users.update = AsyncMock(
            return_value=User(
                id=1, email=Email("new@test.com"), password_hash="hash", full_name="User"
            )
        )

        uc = UpdateUserUseCase(mock_uow_factory, password_service)
        result = await uc.execute(1, email="new@test.com")
        assert result.email == "new@test.com"

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_uow, mock_uow_factory, password_service):
        mock_uow.users.get_by_id = AsyncMock(return_value=None)
        uc = UpdateUserUseCase(mock_uow_factory, password_service)
        with pytest.raises(NotFoundError):
            await uc.execute(999, email="x@y.com")


class TestDeleteUserUseCase:
    @pytest.mark.asyncio
    async def test_deletes_user(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(
            return_value=User(
                id=1, email=Email("del@test.com"), password_hash="hash", full_name="Del User"
            )
        )
        mock_uow.users.delete = AsyncMock()

        uc = DeleteUserUseCase(mock_uow_factory)
        await uc.execute(1)
        mock_uow.users.delete.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(return_value=None)
        uc = DeleteUserUseCase(mock_uow_factory)
        with pytest.raises(NotFoundError):
            await uc.execute(999)


class TestListUsersUseCase:
    @pytest.mark.asyncio
    async def test_returns_all_users(self, mock_uow, mock_uow_factory):
        mock_uow.users.list_all = AsyncMock(
            return_value=[
                User(id=1, email=Email("a@b.com"), password_hash="h1", full_name="A"),
                User(id=2, email=Email("c@d.com"), password_hash="h2", full_name="B"),
            ]
        )
        uc = ListUsersUseCase(mock_uow_factory)
        result = await uc.execute()
        assert len(result) == 2


class TestGetUserAccountsAdminUseCase:
    @pytest.mark.asyncio
    async def test_returns_user_accounts(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(
            return_value=User(id=1, email=Email("u@t.com"), password_hash="h", full_name="U")
        )
        mock_uow.accounts.get_by_user_id = AsyncMock(
            return_value=[Account(id=1, user_id=1, balance=Decimal("100.00"))]
        )
        uc = GetUserAccountsAdminUseCase(mock_uow_factory)
        result = await uc.execute(1)
        assert len(result) == 1
        assert result[0].balance == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(return_value=None)
        uc = GetUserAccountsAdminUseCase(mock_uow_factory)
        with pytest.raises(NotFoundError):
            await uc.execute(999)


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
    async def test_webhook_creates_account_when_missing(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(
            return_value=User(id=1, email=Email("u@t.com"), password_hash="x", full_name="T")
        )
        mock_uow.payments.get_by_transaction_id = AsyncMock(return_value=None)
        mock_uow.accounts.get_by_user_id = AsyncMock(return_value=[])
        mock_uow.accounts.create = AsyncMock(
            return_value=Account(id=10, user_id=1, balance=Decimal("0.00"))
        )
        mock_uow.payments.create_if_not_exists = AsyncMock(
            return_value=(
                Payment(transaction_id="tx-new", user_id=1, account_id=10, amount=Decimal("75.00")),
                True,
            )
        )
        mock_uow.accounts.add_balance = AsyncMock(
            return_value=Account(id=10, user_id=1, balance=Decimal("75.00"))
        )

        config = MagicMock()
        config.secret_key = "sk"
        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        # Signature: {account_id}{amount}{transaction_id}{user_id}{secret_key}
        sig = hashlib.sha256(b"9975tx-new1sk").hexdigest()
        result = await uc.execute("tx-new", 1, 99, Decimal("75.00"), sig)

        assert result.transaction_id == "tx-new"
        mock_uow.accounts.create.assert_awaited_once()
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

    @pytest.mark.asyncio
    async def test_webhook_user_not_found(self, mock_uow, mock_uow_factory):
        mock_uow.users.get_by_id = AsyncMock(return_value=None)
        config = MagicMock()
        config.secret_key = "sk"
        uc = ProcessPaymentWebhookUseCase(mock_uow_factory, config)

        # Signature: {account_id}{amount}{transaction_id}{user_id}{secret_key}
        sig = hashlib.sha256(b"1100tx-1999sk").hexdigest()
        with pytest.raises(NotFoundError):
            await uc.execute("tx-1", 999, 1, Decimal("100.00"), sig)
