"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import Storage
from app.application.auth_service import AuthService
from app.domain.user import UserRole
from pydantic import BaseModel, Field


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Payload for user registration."""
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    """Payload for user login."""
    username: str = Field(max_length=50)
    password: str = Field(max_length=100)


class AuthResponse(BaseModel):
    """Response containing access token."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    storage: Storage,
) -> AuthResponse:
    """Register a new user."""
    # Check if username already exists
    existing_user = await storage.get_user_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = await storage.get_user_by_email(request.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    auth_service = AuthService()
    user = auth_service.create_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )

    # Save to storage
    await storage.save_user(user)

    # Generate token
    access_token = auth_service.create_access_token(
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )

    return AuthResponse(
        access_token=access_token,
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    storage: Storage,
) -> AuthResponse:
    """Login and receive an access token."""
    # Get user by username
    user = await storage.get_user_by_username(request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    auth_service = AuthService()
    if not auth_service.authenticate_user(request.username, request.password, user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    access_token = auth_service.create_access_token(
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )

    return AuthResponse(
        access_token=access_token,
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )
