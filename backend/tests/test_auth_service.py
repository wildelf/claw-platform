"""Tests for auth service."""

import pytest
from app.application.auth_service import AuthService
from app.domain.user import User, UserRole
from app.domain.base import EntityId


class TestPasswordHashing:
    """Tests for password hashing."""

    def test_hash_password_returns_different_value(self):
        """Hashed password should differ from plain text."""
        service = AuthService()
        password = "testpassword123"
        hashed = service.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_is_unique(self):
        """Same password should produce different hashes (salted)."""
        service = AuthService()
        password = "testpassword123"
        hash1 = service.hash_password(password)
        hash2 = service.hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """verify_password returns True for correct password."""
        service = AuthService()
        password = "testpassword123"
        hashed = service.hash_password(password)
        assert service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password returns False for incorrect password."""
        service = AuthService()
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = service.hash_password(password)
        assert service.verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Tests for JWT token operations."""

    def test_create_access_token_returns_string(self):
        """create_access_token returns a non-empty string."""
        service = AuthService()
        token = service.create_access_token(
            user_id="user-123",
            username="testuser",
            role="user",
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """verify_token returns payload for valid token."""
        service = AuthService()
        token = service.create_access_token(
            user_id="user-123",
            username="testuser",
            role="user",
        )
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"

    def test_verify_token_invalid(self):
        """verify_token returns None for invalid token."""
        service = AuthService()
        payload = service.verify_token("invalid.token.here")
        assert payload is None

    def test_verify_token_tampered(self):
        """verify_token returns None for tampered token."""
        service = AuthService()
        token = service.create_access_token(
            user_id="user-123",
            username="testuser",
            role="user",
        )
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        payload = service.verify_token(tampered)
        assert payload is None


class TestUserCreation:
    """Tests for user creation."""

    def test_create_user_hashes_password(self):
        """create_user should hash the password, not store plain text."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="plaintextpassword",
        )
        assert user.password_hash != "plaintextpassword"
        assert user.password_hash.startswith("$2b$")  # bcrypt prefix

    def test_create_user_generates_id(self):
        """create_user should generate a unique ID."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
        )
        assert user.id is not None
        assert len(str(user.id)) == 36  # UUID format

    def test_create_user_default_role(self):
        """create_user should default to USER role."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
        )
        assert user.role == UserRole.USER

    def test_create_user_admin_role(self):
        """create_user should accept admin role."""
        service = AuthService()
        user = service.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password",
            role=UserRole.ADMIN,
        )
        assert user.role == UserRole.ADMIN


class TestAuthenticateUser:
    """Tests for user authentication."""

    def test_authenticate_user_success(self):
        """authenticate_user returns True for valid credentials."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="correctpassword",
        )
        result = service.authenticate_user("testuser", "correctpassword", user)
        assert result is True

    def test_authenticate_user_wrong_password(self):
        """authenticate_user returns False for wrong password."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="correctpassword",
        )
        result = service.authenticate_user("testuser", "wrongpassword", user)
        assert result is False

    def test_authenticate_user_inactive_user(self):
        """authenticate_user returns False for inactive user."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="correctpassword",
        )
        user.is_active = False
        result = service.authenticate_user("testuser", "correctpassword", user)
        assert result is False
