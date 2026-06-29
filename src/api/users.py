"""Router del perfil de usuario (`/users`).

Todas las rutas requieren sesión. La lógica vive en `user_service`; aquí solo
se mapean dependencias y DTOs.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.db import get_session
from src.infra.storage import StorageService, get_storage_service
from src.middleware.auth import CurrentUser, get_current_user
from src.models.dto.users import UserMeDTO, UserUpdateDTO
from src.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeDTO)
async def get_me(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
) -> UserMeDTO:
    return await user_service.get_me(session, storage, uuid.UUID(user.id))


@router.patch("/me", response_model=UserMeDTO)
async def update_me(
    dto: UserUpdateDTO,
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
) -> UserMeDTO:
    return await user_service.update_me(session, storage, uuid.UUID(user.id), dto)


@router.post("/me/photo", response_model=UserMeDTO)
async def upload_photo(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
) -> UserMeDTO:
    data = await file.read()
    return await user_service.set_photo(session, storage, uuid.UUID(user.id), data)


@router.delete("/me/photo", response_model=UserMeDTO)
async def delete_photo(
    session: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
) -> UserMeDTO:
    return await user_service.delete_photo(session, storage, uuid.UUID(user.id))
