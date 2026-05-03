"""Authentication service with JWT and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.domain.user import User, UserRole
from app.domain.base import EntityId


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.auth.jwt.algorithm
SECRET_KEY = settings.auth.jwt.secret
ACCESS_TOKEN_EXPIRE_MINUTES = settings.auth.jwt.expire_minutes


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        pass

    def hash_password(self, plain_password: str) -> str:
        """Hash a plain password using bcrypt."""
        return pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: str, username: str, role: str) -> str:
        """Create a JWT access token."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode a JWT token. Returns payload if valid, None if invalid."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def create_user(self, username: str, email: str, password: str, role: UserRole = UserRole.USER) -> User:
        """Create a new user with hashed password."""
        return User(
            id=EntityId.generate(),
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            role=role,
            is_active=True,
        )

    def authenticate_user(self, username: str, password: str, user: User) -> bool:
        """Authenticate a user by username and password."""
        if not user.is_active:
            return False
        return self.verify_password(password, user.password_hash)