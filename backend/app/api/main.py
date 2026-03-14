from fastapi import APIRouter

from app.api.routes import clients, login, permissions, private, services, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(clients.router)
api_router.include_router(services.router)
api_router.include_router(permissions.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
