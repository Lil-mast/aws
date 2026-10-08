"""
app/users/schemas/__init__.py
─────────────────────────────
Pydantic request / response schemas for the users app.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class RegisterResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Google OAuth ──────────────────────────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    """Client sends the Google ID token obtained from Google Sign-In."""
    id_token: str


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    phone_number: Optional[str]
    currency: str
    is_verified: bool
    oauth_provider: Optional[str]
    created_at: datetime
    # Nested profile fields (may be None until profile is created)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    monthly_income: Optional[float] = None
    employment_type: Optional[str] = None
    score_consent: bool = False

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    currency: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    monthly_income: Optional[float] = None
    employment_type: Optional[str] = None
    score_consent: Optional[bool] = None
