from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user, current_admin_user
from app.core.database import get_db_session
from app.models import User
from app.schemas.user import UserCreate, UserRead, UserUpdate, UsersPage
from app.services import UserService

router = APIRouter()


@router.get("/", response_model=UsersPage, summary="List users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> UsersPage:
    service = UserService(session)
    limit = page_size
    offset = (page - 1) * limit
    users, total = await service.list_users(limit=limit, offset=offset)
    return UsersPage(
        items=[UserRead.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=limit,
    )


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(
    payload: UserCreate,
    _: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserRead:
    service = UserService(session)
    user = await service.create_user(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        is_active=payload.is_active,
        preferences=payload.preferences,
        feature_flags=payload.feature_flags,
    )
    await session.commit()
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead, summary="Retrieve user by id")
async def get_user(
    user_id: uuid.UUID,
    _: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserRead:
    service = UserService(session)
    user = await service.get_user(user_id)
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead, summary="Update a user")
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    _: User = Depends(current_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserRead:
    service = UserService(session)
    user = await service.get_user(user_id)
    updated = await service.update_user(user, payload=payload.model_dump(exclude_unset=True))
    await session.commit()
    return UserRead.model_validate(updated)


@router.patch("/me", response_model=UserRead, summary="Update current user profile")
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserRead:
    allowed = payload.model_dump(exclude_unset=True)
    allowed.pop("role", None)
    allowed.pop("is_active", None)
    allowed.pop("password", None)
    service = UserService(session)
    user = await service.get_user(current_user.id)
    updated = await service.update_user(user, payload=allowed)
    await session.commit()
    return UserRead.model_validate(updated)
