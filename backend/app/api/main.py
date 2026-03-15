from fastapi import APIRouter

from app.api.routes import (
    clients,
    estoque,
    fornecedores,
    login,
    orcamentos,
    permissions,
    private,
    product_items,
    product_types,
    products,
    services,
    transacoes,
    users,
    utils,
)
from app.api.routes import (
    settings as settings_routes,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(clients.router)
api_router.include_router(services.router)
api_router.include_router(permissions.router)
api_router.include_router(transacoes.router)
api_router.include_router(fornecedores.router)
api_router.include_router(product_types.router)
api_router.include_router(products.router)
api_router.include_router(product_items.router)
api_router.include_router(estoque.router)
api_router.include_router(orcamentos.router)
api_router.include_router(settings_routes.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
