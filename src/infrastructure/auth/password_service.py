import bcrypt


class PasswordService:
    def hash(self, plain_password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain_password.encode(), salt).decode()

    def verify(self, plain_password: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain_password.encode(), hashed.encode())
