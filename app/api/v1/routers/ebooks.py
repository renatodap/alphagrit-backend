from fastapi import APIRouter, Depends, Header
from typing import Optional

from app.api.v1.deps.auth import get_current_user
from app.services.ebooks import ebooks_service
from app.api.v1.dto.ebook_dto import EbookOut
from app.core.auth import verifier

router = APIRouter()


@router.get("")
async def list_ebooks():
    return await ebooks_service.list_ebooks()


@router.get("/{slug}")
async def get_ebook(slug: str, authorization: Optional[str] = Header(None)):
    """
    Get ebook details. Works for both authenticated and guest users.
    If authenticated, includes ownership status.
    """
    user = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            user = await verifier.verify(token)
        except Exception:
            pass  # Guest user - no auth

    return await ebooks_service.get_ebook_by_slug(slug, user)


@router.post("/checkout/ebooks/{ebook_id}")
async def checkout_ebook(ebook_id: int, user=Depends(get_current_user)):
    return await ebooks_service.create_checkout(ebook_id, user["sub"])  # type: ignore[index]


@router.post("/checkout/combo/{ebook_id}")
async def checkout_combo(ebook_id: int, tier: str = "standard", user=Depends(get_current_user)):
    if tier not in ("standard", "premium"):
        tier = "standard"
    return await ebooks_service.create_combo_checkout(ebook_id, user["sub"], tier)  # type: ignore[index]
