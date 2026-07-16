from sanic import Sanic, response
from sanic.request import Request


def setup_cors(app: Sanic) -> None:
    """Add CORS headers to all responses via middleware.

    Allows all origins, methods, and common headers — suitable for
    development and test assignments. Tighten for production.
    """

    @app.middleware("request")
    async def handle_cors_options(request: Request):
        if request.method == "OPTIONS":
            headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600",
            }
            return response.empty(headers=headers)

    @app.middleware("response")
    async def add_cors_headers(_request: Request, resp):
        resp.headers.setdefault("Access-Control-Allow-Origin", "*")
        resp.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization")
