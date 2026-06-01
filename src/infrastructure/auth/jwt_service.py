from datetime import datetime, timedelta
from typing import Any

import jwt

from src.infrastructure.config import AppConfig


class JwtService:
    def __init__(self, config: AppConfig):
        self._config = config

    def create_access_token(self, user_id: int, role: str) -> str:
        payload: dict[str, Any] = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.utcnow()
            + timedelta(minutes=self._config.jwt_expiry_minutes),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(
            payload, self._config.jwt_secret, algorithm=self._config.jwt_algorithm
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(
            token,
            self._config.jwt_secret,
            algorithms=[self._config.jwt_algorithm],
        )
