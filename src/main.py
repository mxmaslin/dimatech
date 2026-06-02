from sanic import Blueprint, Sanic, response

from src.container import Container
from src.infrastructure.config import AppConfig
from src.presentation.errors import setup_error_handlers
from src.presentation.middleware import setup_middleware
from src.presentation.routes.admin import setup_admin_routes
from src.presentation.routes.auth import setup_auth_routes
from src.presentation.routes.payment import setup_payment_routes
from src.presentation.routes.user import setup_user_routes


def create_app(config: AppConfig | None = None) -> Sanic:
    if config is None or not isinstance(config, AppConfig):
        config = AppConfig()

    app = Sanic("DimaTech")

    container = Container(config)

    app.ctx.container = container
    app.ctx.config = config

    auth_middleware = setup_middleware(app, container.jwt_service)

    # Create fresh blueprints so create_app is re-entrant safe (e.g. in tests)
    auth_bp = Blueprint("auth", url_prefix="/auth")
    users_bp = Blueprint("users", url_prefix="/users")
    payment_bp = Blueprint("payment", url_prefix="/payments")

    setup_auth_routes(
        auth_bp,
        container.login_use_case(),
        container.get_admin_use_case(),
        auth_middleware,
    )

    # All user+admin routes share /users prefix under a single blueprint
    setup_user_routes(
        users_bp,
        container.get_user_use_case(),
        container.get_user_accounts_use_case(),
        container.get_user_payments_use_case(),
        auth_middleware,
    )

    setup_admin_routes(
        users_bp,
        container.create_user_use_case(),
        container.update_user_use_case(),
        container.delete_user_use_case(),
        container.list_users_use_case(),
        container.get_user_accounts_admin_use_case(),
        auth_middleware,
    )

    setup_payment_routes(
        payment_bp,
        container.process_payment_use_case(),
    )

    app.blueprint(auth_bp)
    app.blueprint(users_bp)
    app.blueprint(payment_bp)

    setup_error_handlers(app)

    @app.get("/health")
    async def health(_request):
        return response.json({"status": "ok"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=app.ctx.config.debug)
