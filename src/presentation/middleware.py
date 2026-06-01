from typing import Optional

import jwt
from sanic import Sanic
from sanic.request import Request

from src.application.errors import AuthenticationError, AuthorizationError


class AuthMiddleware:
    def __init__(self, jwt_secret: str, jwt_algorithm: str):
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm

    def _get_token(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    def _decode(self, token: str) -> dict:
        try:
            return jwt.decode(
                token, self._jwt_secret, algorithms=[self._jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

    def require_auth(self, request: Request) -> dict:
        token = self._get_token(request)
        if not token:
            raise AuthenticationError("Missing authorization header")
        payload = self._decode(token)
        request.ctx.user_id = payload.get("user_id")
        request.ctx.role = payload.get("role")
        return payload

    def require_admin(self, request: Request) -> dict:
        payload = self.require_auth(request)
        if payload.get("role") != "admin":
            raise AuthorizationError("Admin access required")
        return payload


def setup_middleware(app: Sanic, jwt_secret: str, jwt_algorithm: str) -> AuthMiddleware:
    auth_middleware = AuthMiddleware(jwt_secret, jwt_algorithm)
    return auth_middleware
