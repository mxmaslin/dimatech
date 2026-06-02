from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    database_url: str = "postgresql+asyncpg://dimatech:dimatech@localhost:5432/dimatech"
    secret_key: str = "gfdmhghif38yrf9ew0jkf32"
    jwt_secret: str = "please-change-this-jwt-secret-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    debug: bool = True
    db_pool_size: int = 5
    db_max_overflow: int = 10

    def __post_init__(self) -> None:
        if len(self.jwt_secret) < 32:
            raise ValueError(
                f"JWT_SECRET must be at least 32 characters, got {len(self.jwt_secret)}"
            )
        if len(self.secret_key) < 16:
            raise ValueError(
                f"SECRET_KEY must be at least 16 characters, got {len(self.secret_key)}"
            )

    model_config = {"env_file": ".env", "extra": "ignore"}
