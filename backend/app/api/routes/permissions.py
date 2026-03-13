import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app import crud
from app.api.deps import SessionDep, require_permission
from app.core.permissions import ALL_PERMISSIONS, get_role_defaults
from app.models import User

router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
    dependencies=[Depends(require_permission("manage_permissions"))],
)


class UserPermissionsOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    is_superuser: bool
    role_defaults: list[str]
    overrides: list[str]
    effective: list[str]


class SetPermissionsIn(BaseModel):
    permissions: list[str]


def _build_user_permissions_out(user: User) -> UserPermissionsOut:
    role_defaults = sorted(get_role_defaults(user.role))
    overrides = sorted({up.permission for up in user.user_permissions})
    effective = sorted(set(role_defaults) | set(overrides))
    return UserPermissionsOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_superuser=user.is_superuser,
        role_defaults=role_defaults,
        overrides=overrides,
        effective=effective,
    )


@router.get("/available")
def get_available_permissions() -> dict[str, str]:
    return ALL_PERMISSIONS


@router.get("/users", response_model=list[UserPermissionsOut])
def get_users_permissions(session: SessionDep) -> Any:
    statement = select(User).options(selectinload(User.user_permissions))  # type: ignore[arg-type]
    users = session.exec(statement).all()
    return [_build_user_permissions_out(u) for u in users]


@router.get("/users/{user_id}", response_model=UserPermissionsOut)
def get_user_permissions(user_id: uuid.UUID, session: SessionDep) -> Any:
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_permissions))  # type: ignore[arg-type]
    )
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _build_user_permissions_out(user)


@router.put("/users/{user_id}", response_model=UserPermissionsOut)
def set_user_permissions(
    user_id: uuid.UUID, body: SetPermissionsIn, session: SessionDep
) -> Any:
    # Validate permissions
    invalid = [p for p in body.permissions if p not in ALL_PERMISSIONS]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Invalid permissions: {invalid}")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    crud.set_user_permissions(
        session=session, user_id=user_id, permissions=body.permissions
    )

    # Re-fetch with relationship loaded
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_permissions))  # type: ignore[arg-type]
    )
    user = session.exec(statement).one()
    return _build_user_permissions_out(user)
