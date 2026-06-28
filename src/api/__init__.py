"""Router raíz de la API.

Agrega aquí los routers de cada módulo a medida que se implementen las fases:
    api_router.include_router(auth_router)
    api_router.include_router(campanas_router)
"""

from fastapi import APIRouter

from src.api.auth import router as auth_router
from src.api.onboarding import router as onboarding_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
