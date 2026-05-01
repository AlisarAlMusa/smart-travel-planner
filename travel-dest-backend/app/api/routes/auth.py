"""Authentication routes for signup and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db import crud
from app.api.dependencies import get_app_settings, get_db
from app.schemas.auth import TokenResponse, UserLoginRequest, UserResponse, UserSignupRequest


router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: UserSignupRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> TokenResponse:
    """Create a new user account and immediately return a JWT."""
    existing_user = crud.get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    user = crud.create_user(db, payload.email, hash_password(payload.password))
    token = create_access_token(str(user.id), settings)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> TokenResponse:
    """Authenticate an existing user and return a JWT."""
    user = crud.get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(str(user.id), settings)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
