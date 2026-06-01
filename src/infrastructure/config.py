from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    database_url: str = "postgresql+asyncpg://dimatech:dimatech@localhost:5432/dimatech"
    secret_key: str = "gfdmhghif38yrf9ew0jkf32"
    jwt_secret: str = "super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    debug: bool = True

    default_user_email: str = "user@example.com"
    default_user_password: str = "user123"
    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "admin123"

    model_config = {"env_file": ".env", "extra": "ignore"}
