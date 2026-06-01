from datetime import datetime
from decimal import Decimal

from src.domain.entities import Account, Payment, User
from src.domain.value_objects import Email


class TestUser:
    def test_create_user(self):
        user = User(
            email=Email("user@example.com"),
            password_hash="hashed_pwd",
            full_name="Test User",
        )
        assert str(user.email) == "user@example.com"
        assert user.is_active is True
        assert user.id is None
        assert isinstance(user.created_at, datetime)


class TestAccount:
    def test_create_account(self):
        account = Account(user_id=1)
        assert account.user_id == 1
        assert account.balance == Decimal("0.00")
        assert account.id is None

    def test_account_with_balance(self):
        account = Account(user_id=1, balance=Decimal("100.50"))
        assert account.balance == Decimal("100.50")


class TestPayment:
    def test_create_payment(self):
        payment = Payment(
            transaction_id="tx-123",
            user_id=1,
            account_id=1,
            amount=Decimal("50.00"),
        )
        assert payment.transaction_id == "tx-123"
        assert payment.amount == Decimal("50.00")
