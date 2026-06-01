from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user_id: int
    role: str


class UserCreateRequest(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserUpdateRequest(BaseModel):
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class AdminResponse(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class AccountResponse(BaseModel):
    id: int
    user_id: int
    balance: Decimal

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentWebhookRequest(BaseModel):
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    signature: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
