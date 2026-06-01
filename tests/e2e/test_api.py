import hashlib
import pytest
from decimal import Decimal

from src.domain.entities import User, Account
from src.domain.value_objects import Email


@pytest.mark.asyncio
async def test_webhook_endpoint(test_client, uow_factory):
    async with uow_factory() as uow:
        user = await uow.users.create(
            User(
                email=Email("webhook@test.com"),
                password_hash="hash",
                full_name="Webhook User",
            )
        )
        account = await uow.accounts.create(
            Account(user_id=user.id, balance=Decimal("0.00"))
        )

    transaction_id = "test-tx-001"
    amount = Decimal("200.00")
    # JSON serializes float(200.00) as 200.0; Pydantic parses to Decimal("200.0")
    # which f-strings as "200.0", so use that in signature computation
    json_amount = float(amount)
    raw = f"{account.id}{json_amount}{transaction_id}{user.id}gfdmhghif38yrf9ew0jkf32"
    signature = hashlib.sha256(raw.encode()).hexdigest()

    request_data = {
        "transaction_id": transaction_id,
        "user_id": user.id,
        "account_id": account.id,
        "amount": json_amount,
        "signature": signature,
    }

    _, response = await test_client.post(
        "/payments/webhook", json=request_data
    )
    assert response.status == 201
    body = response.json
    assert body["transaction_id"] == transaction_id


@pytest.mark.asyncio
async def test_login_and_get_me(test_client):
    _, login_resp = await test_client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "user123"},
    )
    assert login_resp.status == 200
    token = login_resp.json["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    _, me_resp = await test_client.get("/users/me", headers=headers)
    assert me_resp.status == 200
    assert me_resp.json["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_admin_login_and_list_users(test_client):
    _, login_resp = await test_client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert login_resp.status == 200
    token = login_resp.json["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    _, users_resp = await test_client.get("/users/", headers=headers)
    assert users_resp.status == 200
    assert len(users_resp.json) >= 1


@pytest.mark.asyncio
async def test_unauthorized_access(test_client):
    _, resp = await test_client.get("/users/me")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_admin_creates_user(test_client):
    _, login_resp = await test_client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    token = login_resp.json["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    _, create_resp = await test_client.post(
        "/users/",
        headers=headers,
        json={
            "email": "newuser@test.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert create_resp.status == 201
    assert create_resp.json["email"] == "newuser@test.com"
