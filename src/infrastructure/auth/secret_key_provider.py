"""Adapter that exposes only the secret key from config.

This preserves Clean Architecture boundaries by keeping infrastructure types
out of the application layer.
"""


class SecretKeyProvider:
    def __init__(self, secret_key: str) -> None:
        self._secret_key = secret_key

    @property
    def secret_key(self) -> str:
        return self._secret_key
