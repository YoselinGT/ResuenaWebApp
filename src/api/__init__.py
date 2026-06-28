"""Router raíz de la API.

Agrega aquí los routers de cada módulo a medida que se implementen las fases:
    api_router.include_router(auth_router)
    api_router.include_router(campanas_router)
"""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api")
