"""Router raíz de la API.

Agrega aquí los routers de cada módulo a medida que se implementen las fases:
    api_router.include_router(auth_router)
    api_router.include_router(campanas_router)
"""

from fastapi import APIRouter

from src.api.admin_paquetes import router as admin_paquetes_router
from src.api.admin_solicitudes import router as admin_solicitudes_router
from src.api.admin_usuarios import router as admin_usuarios_router
from src.api.auth import router as auth_router
from src.api.config_public import router as config_router
from src.api.creditos import router as creditos_router
from src.api.curador_medios import router as curador_medios_router
from src.api.onboarding import router as onboarding_router
from src.api.sellos import router as sellos_router
from src.api.users import router as users_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(users_router)
api_router.include_router(config_router)
api_router.include_router(sellos_router)
api_router.include_router(curador_medios_router)
api_router.include_router(creditos_router)
api_router.include_router(admin_paquetes_router)
api_router.include_router(admin_solicitudes_router)
api_router.include_router(admin_usuarios_router)
