from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps.auth import get_current_user
from app.services.admin import admin_service

router = APIRouter()


def require_admin(user):
    if "admin" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/analytics/sales")
async def analytics_sales(user=Depends(get_current_user)):
    require_admin(user)
    return await admin_service.analytics_sales()


@router.get("/analytics/programs")
async def analytics_programs(user=Depends(get_current_user)):
    require_admin(user)
    return await admin_service.analytics_programs()


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, user=Depends(get_current_user)):
    require_admin(user)
    return await admin_service.delete_post(post_id)
