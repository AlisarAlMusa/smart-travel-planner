"""Schemas for signup, login, and authenticated user responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserSignupRequest(BaseModel):
    """Request body for creating a user account."""

    email: EmailStr
    password: str = Field(min_length=8)


class UserLoginRequest(BaseModel):
    """Request body for logging a user in."""

    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    """Safe user data returned by the API."""

    id: UUID
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token returned after signup or login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse

