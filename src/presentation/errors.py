from pydantic import ValidationError as PydanticValidationError
from sanic import Sanic, response
from sanic.exceptions import SanicException
from sanic.request import Request

from src.application.errors import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    DuplicateError,
    NotFoundError,
    SignatureVerificationError,
    ValidationError,
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
    async def handle_signature_error(_request: Request, exception: SignatureVerificationError):
        return response.json(
            {"error": "invalid_signature", "detail": exception.message},
            status=400,
        )

    @app.exception(ValidationError)
    async def handle_validation_error(_request: Request, exception: ValidationError):
        return response.json(
            {"error": "validation_error", "detail": exception.message},
            status=400,
        )

    @app.exception(ApplicationError)
    async def handle_application_error(_request: Request, exception: ApplicationError):
        return response.json(
            {"error": "application_error", "detail": exception.message},
            status=exception.status_code,
        )

    @app.exception(SanicException)
    async def handle_sanic_error(_request: Request, exception: SanicException):
        status = exception.status_code
        if status < 500:
            error = "bad_request"
        else:
            error = "internal_error"
        return response.json(
            {"error": error, "detail": str(exception)},
            status=status,
        )

    @app.exception(PydanticValidationError)
    async def handle_pydantic_validation_error(
        _request: Request, exception: PydanticValidationError
    ):
        return response.json(
            {"error": "validation_error", "detail": str(exception)},
            status=422,
        )
