from typing import Optional

from sanic import Sanic
from sanic.request import Request

from src.application.errors import AuthenticationError, AuthorizationError
from src.domain.interfaces import JwtService


class AuthMiddleware:
    def __init__(self, jwt_service: JwtService):
        self._jwt_service = jwt_service

    def _get_token(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    def require_auth(self, request: Request) -> dict:
        token = self._get_token(request)
        if not token:
            raise AuthenticationError("Missing authorization header")
        payload = self._jwt_service.decode_token(token)
        request.ctx.user_id = payload.get("user_id")
        request.ctx.role = payload.get("role")
        return payload

    def require_user(self, request: Request) -> dict:
        payload = self.require_auth(request)
        if payload.get("role") != "user":
            raise AuthorizationError("User access required")
        return payload

    def require_admin(self, request: Request) -> dict:
        payload = self.require_auth(request)
        if payload.get("role") != "admin":
            raise AuthorizationError("Admin access required")
        return payload


def setup_middleware(app: Sanic, jwt_service: JwtService) -> AuthMiddleware:
    auth_middleware = AuthMiddleware(jwt_service)
    return auth_middleware
