from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps.auth import get_current_user
from app.services.affiliate import affiliate_service

router = APIRouter()


@router.get("/products")
async def list_products():
    return await affiliate_service.list_products()


@router.post("/products")
async def create_product(payload: dict, user=Depends(get_current_user)):
    if "admin" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")
    return await affiliate_service.create_product(payload)


@router.put("/products/{product_id}")
async def update_product(product_id: int, payload: dict, user=Depends(get_current_user)):
    if "admin" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")
    return await affiliate_service.update_product(product_id, payload)


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, user=Depends(get_current_user)):
    if "admin" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")
    return await affiliate_service.delete_product(product_id)
