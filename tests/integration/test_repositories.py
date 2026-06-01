from decimal import Decimal

import pytest

from src.domain.entities import Account, Payment, User
from src.domain.value_objects import Email
from src.infrastructure.database.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyPaymentRepository,
    SqlAlchemyUserRepository,
)


@pytest.mark.asyncio
async def test_user_repository_create_and_get(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user = User(
        email=Email("test@example.com"),
        password_hash="hashed",
        full_name="Test User",
    )
    created = await repo.create(user)
    assert created.id is not None
    assert str(created.email) == "test@example.com"

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.full_name == "Test User"

    by_email = await repo.get_by_email("test@example.com")
    assert by_email is not None
    assert by_email.id == created.id


@pytest.mark.asyncio
async def test_user_repository_update(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user = User(
        email=Email("update@example.com"),
        password_hash="oldhash",
        full_name="Old Name",
    )
    created = await repo.create(user)
    created.full_name = "New Name"
    updated = await repo.update(created)
    assert updated.full_name == "New Name"

    fetched = await repo.get_by_id(created.id)
    assert fetched.full_name == "New Name"


@pytest.mark.asyncio
async def test_user_repository_delete(db_session):
    repo = SqlAlchemyUserRepository(db_session)
    user = User(
        email=Email("delete@example.com"),
        password_hash="hash",
        full_name="Delete Me",
    )
    created = await repo.create(user)
    await repo.delete(created.id)
    fetched = await repo.get_by_id(created.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_account_repository(db_session):
    user_repo = SqlAlchemyUserRepository(db_session)
    acc_repo = SqlAlchemyAccountRepository(db_session)

    user = await user_repo.create(
        User(email=Email("accuser@test.com"), password_hash="h", full_name="Acc User")
    )

    account = Account(user_id=user.id, balance=Decimal("50.00"))
    created = await acc_repo.create(account)
    assert created.id is not None
    assert created.balance == Decimal("50.00")

    accounts = await acc_repo.get_by_user_id(user.id)
    assert len(accounts) == 1

    updated = await acc_repo.add_balance(created.id, Decimal("25.00"))
    assert updated.balance == Decimal("75.00")


@pytest.mark.asyncio
async def test_payment_repository(db_session):
    user_repo = SqlAlchemyUserRepository(db_session)
    acc_repo = SqlAlchemyAccountRepository(db_session)
    pay_repo = SqlAlchemyPaymentRepository(db_session)

    user = await user_repo.create(
        User(
            email=Email("payuser@test.com"),
            password_hash="h",
            full_name="Pay User",
        )
    )
    account = await acc_repo.create(Account(user_id=user.id, balance=Decimal("0.00")))

    payment = Payment(
        transaction_id="tx-unique-123",
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("100.00"),
    )
    created = await pay_repo.create(payment)
    assert created.transaction_id == "tx-unique-123"

    fetched = await pay_repo.get_by_transaction_id("tx-unique-123")
    assert fetched is not None
    assert fetched.amount == Decimal("100.00")

    payments = await pay_repo.get_by_user_id(user.id)
    assert len(payments) == 1


@pytest.mark.asyncio
async def test_payment_create_if_not_exists(db_session):
    user_repo = SqlAlchemyUserRepository(db_session)
    acc_repo = SqlAlchemyAccountRepository(db_session)
    pay_repo = SqlAlchemyPaymentRepository(db_session)

    user = await user_repo.create(
        User(
            email=Email("idempotent-repo@test.com"),
            password_hash="h",
            full_name="Idempotent User",
        )
    )
    account = await acc_repo.create(Account(user_id=user.id, balance=Decimal("0.00")))

    payment = Payment(
        transaction_id="tx-idempotent-456",
        user_id=user.id,
        account_id=account.id,
        amount=Decimal("25.00"),
    )
    created, was_created = await pay_repo.create_if_not_exists(payment)
    assert was_created is True
    assert created.transaction_id == "tx-idempotent-456"

    duplicate, was_created = await pay_repo.create_if_not_exists(payment)
    assert was_created is False
    assert duplicate.transaction_id == "tx-idempotent-456"

    payments = await pay_repo.get_by_user_id(user.id)
    assert len(payments) == 1
