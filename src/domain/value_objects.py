import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid email address: {self.value}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Password:
    value: str

    def __post_init__(self) -> None:
        if len(self.value) < 6:
            raise ValueError("Password must be at least 6 characters long")

    def __str__(self) -> str:
        return "***"  # Never expose password value
