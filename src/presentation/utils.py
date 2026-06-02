from sanic.request import Request

from src.application.errors import ValidationError


def require_json(request: Request) -> dict:
    data = request.json
    if data is None:
        raise ValidationError("Request body must be valid JSON")
    return data
