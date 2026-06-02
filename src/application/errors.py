class ApplicationError(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(ApplicationError):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, status_code=401)


class AuthorizationError(ApplicationError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class NotFoundError(ApplicationError):
    def __init__(self, entity: str = "Resource"):
        super().__init__(f"{entity} not found", status_code=404)


class ValidationError(ApplicationError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=400)


class DuplicateError(ApplicationError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)


class SignatureVerificationError(ApplicationError):
    def __init__(self, message: str = "Invalid signature"):
        super().__init__(message, status_code=400)


class InternalError(ApplicationError):
    """Error representing an unexpected internal state (should never happen)."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)
