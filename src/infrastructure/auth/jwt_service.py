from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

from src.infrastructure.config import AppConfig


class JwtService:
    def __init__(self, config: AppConfig):
        self._config = config

    def create_access_token(self, user_id: int, role: str) -> str:
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "user_id": user_id,
            "role": role,
            "exp": now + timedelta(minutes=self._config.jwt_expiry_minutes),
            "iat": now,
        }
        return jwt.encode(payload, self._config.jwt_secret, algorithm=self._config.jwt_algorithm)

    def decode_token(self, token: str) -> Optional[dict[str, Any]]:
        """Decode and validate a JWT token.

        Returns the decoded payload on success, or None on any validation failure.
        The caller is responsible for raising appropriate errors.
        """
        try:
            return jwt.decode(
                token,
                self._config.jwt_secret,
                algorithms=[self._config.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
