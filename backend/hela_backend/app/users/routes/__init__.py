"""
app/users/routes/__init__.py
────────────────────────────
Authentication and profile endpoints.

Routes (all prefixed /api/v1/auth by main.py):
  POST   /register
  POST   /login
  POST   /logout
  POST   /token/refresh
  POST   /google
  GET    /profile
  PUT    /profile/update
"""

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import RefreshToken, User, UserProfile
from app.users.schemas import (
    GoogleAuthRequest,
    LoginRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from core.config import get_settings
from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])
settings = get_settings()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_token(token: str) -> str:
    """SHA-256 of a refresh token for safe storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def _issue_token_pair(user: User, db: AsyncSession) -> TokenResponse:
    """Create access + refresh tokens, persist the refresh token hash."""
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(refresh),
            expires_at=expires,
        )
    )
    await db.flush()
    return TokenResponse(access_token=access, refresh_token=refresh)


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new email/password account."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()                          # get user.id before profile insert
    db.add(UserProfile(user_id=user.id))
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Email/password login — returns JWT access + refresh tokens."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive.")

    return await _issue_token_pair(user, db)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=204)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Revoke the supplied refresh token."""
    token_hash = _hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()
    if rt:
        rt.revoked = True


# ── Token refresh ─────────────────────────────────────────────────────────────

@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair (rotation)."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type.")

    token_hash = _hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    rt = result.scalar_one_or_none()

    if not rt or rt.revoked:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked.")
    if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token has expired.")

    # Revoke old token and issue a new pair (rotation)
    rt.revoked = True
    user_result = await db.execute(select(User).where(User.id == UUID(payload["sub"])))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found.")

    return await _issue_token_pair(user, db)


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify a Google ID token from the frontend and return Hela JWT tokens.
    The client obtains the ID token via Google Sign-In (one-tap or redirect).
    """
    try:
        id_info = google_id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {exc}")

    email: str = id_info["email"]
    google_sub: str = id_info["sub"]
    full_name: str = id_info.get("name", "")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # First-time Google sign-in → create account
        user = User(
            email=email,
            full_name=full_name,
            is_verified=True,
            oauth_provider="google",
            oauth_subject=google_sub,
        )
        db.add(user)
        await db.flush()
        db.add(UserProfile(user_id=user.id))
    else:
        # Returning user — update OAuth fields if needed
        if not user.oauth_subject:
            user.oauth_provider = "google"
            user.oauth_subject = google_sub

    return await _issue_token_pair(user, db)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    resp = ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        currency=current_user.currency,
        is_verified=current_user.is_verified,
        oauth_provider=current_user.oauth_provider,
        created_at=current_user.created_at,
    )
    if profile:
        resp.bio = profile.bio
        resp.avatar_url = profile.avatar_url
        resp.monthly_income = profile.monthly_income
        resp.employment_type = profile.employment_type
        resp.score_consent = profile.score_consent
    return resp


@router.put("/profile/update", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user and profile fields."""
    # Update User fields
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.phone_number is not None:
        current_user.phone_number = body.phone_number
    if body.currency is not None:
        current_user.currency = body.currency

    # Update or create UserProfile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if body.bio is not None:
        profile.bio = body.bio
    if body.avatar_url is not None:
        profile.avatar_url = body.avatar_url
    if body.monthly_income is not None:
        profile.monthly_income = body.monthly_income
    if body.employment_type is not None:
        profile.employment_type = body.employment_type
    if body.score_consent is not None:
        profile.score_consent = body.score_consent

    await db.flush()
    return await get_profile(current_user, db)
