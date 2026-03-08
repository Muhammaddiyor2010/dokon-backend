from fastapi import APIRouter

from app.api import admin, auth, catalog, orders

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(catalog.router, tags=["catalog"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
