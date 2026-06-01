from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from src.domain.value_objects import Email


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    email: Email
    password_hash: str
    full_name: str
    is_active: bool = True
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class Admin:
    email: Email
    password_hash: str
    full_name: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class Account:
    user_id: int
    balance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    id: Optional[int] = None
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class Payment:
    transaction_id: str
    user_id: int
    account_id: int
    amount: Decimal
    created_at: datetime = field(default_factory=_utcnow)
