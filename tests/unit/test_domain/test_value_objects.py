import pytest

from src.domain.value_objects import Email, Password


class TestEmail:
    def test_valid_email(self):
        email = Email("user@example.com")
        assert str(email) == "user@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Email("not-an-email")

    def test_equality(self):
        e1 = Email("test@example.com")
        e2 = Email("test@example.com")
        assert e1 == e2

    def test_hashable(self):
        emails = {Email("a@b.com"), Email("a@b.com")}
        assert len(emails) == 1


class TestPassword:
    def test_valid_password(self):
        pwd = Password("abcdef")
        assert str(pwd) == "***"

    def test_short_password(self):
        with pytest.raises(ValueError, match="at least 6"):
            Password("abc12")
