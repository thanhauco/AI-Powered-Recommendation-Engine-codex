from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthService, current_active_user
from app.core.database import get_db_session
from app.core.security import verify_password
from app.models import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    SignupRequest,
    TokenRefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserRead

router = APIRouter()


@router.post("/token", response_model=TokenResponse, summary="Login via OAuth2 password flow")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    service = AuthService(session)
    user = await service.authenticate(email=form_data.username, password=form_data.password)
    await session.commit()
    access, refresh = await service.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse, summary="Login with JSON payload")
async def login_with_json(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    service = AuthService(session)
    user = await service.authenticate(email=payload.email, password=payload.password)
    await session.commit()
    access, refresh = await service.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh JWT tokens")
async def refresh_tokens(
    payload: TokenRefreshRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    service = AuthService(session)
    access, refresh = await service.refresh_tokens(payload.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def signup(
    payload: SignupRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    service = AuthService(session)
    user = await service.create_user(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=UserRole.USER,
    )
    await session.commit()
    access, refresh = await service.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserRead, summary="Retrieve current user profile")
async def read_me(current_user: User = Depends(current_active_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/change-password", response_model=TokenResponse, summary="Change password for current user")
async def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    service = AuthService(session)
    await service.change_password(current_user, new_password=payload.new_password)
    await session.commit()
    access, refresh = await service.issue_tokens(current_user)
    return TokenResponse(access_token=access, refresh_token=refresh)
