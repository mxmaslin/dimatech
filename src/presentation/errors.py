from sanic import Sanic, response
from sanic.request import Request

from src.application.errors import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    DuplicateError,
    NotFoundError,
    SignatureVerificationError,
)


def setup_error_handlers(app: Sanic) -> None:
    @app.exception(NotFoundError)
    async def handle_not_found(_request: Request, exception: NotFoundError):
        return response.json(
            {"error": "not_found", "detail": exception.message},
            status=404,
        )

    @app.exception(AuthenticationError)
    async def handle_auth_error(_request: Request, exception: AuthenticationError):
        return response.json(
            {"error": "unauthorized", "detail": exception.message},
            status=401,
        )

    @app.exception(AuthorizationError)
    async def handle_forbidden(_request: Request, exception: AuthorizationError):
        return response.json(
            {"error": "forbidden", "detail": exception.message},
            status=403,
        )

    @app.exception(DuplicateError)
    async def handle_duplicate(_request: Request, exception: DuplicateError):
        return response.json(
            {"error": "conflict", "detail": exception.message},
            status=409,
        )

    @app.exception(SignatureVerificationError)
    async def handle_signature_error(
        _request: Request, exception: SignatureVerificationError
    ):
        return response.json(
            {"error": "invalid_signature", "detail": exception.message},
            status=400,
        )

    @app.exception(ApplicationError)
    async def handle_application_error(
        _request: Request, exception: ApplicationError
    ):
        return response.json(
            {"error": "application_error", "detail": exception.message},
            status=exception.status_code,
        )
