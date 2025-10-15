from fastapi import APIRouter, Depends

from app.api.v1.deps.auth import get_current_user
from app.services.programs import program_service
from app.api.v1.dto.post_dto import CreatePostIn

router = APIRouter()


@router.get("")
async def list_programs():
    return await program_service.list_programs()


@router.get("/{program_id}")
async def get_program(program_id: int, user=Depends(get_current_user)):
    return await program_service.get_program(program_id, user)


@router.get("/{program_id}/posts")
async def list_posts(program_id: int, user=Depends(get_current_user)):
    from app.services.posts import posts_service

    return await posts_service.list_posts(program_id, user)


@router.post("/{program_id}/posts")
async def create_post(program_id: int, payload: CreatePostIn, user=Depends(get_current_user)):
    from app.services.posts import posts_service

    return await posts_service.create_post(program_id, payload.model_dump(), user)


@router.post("/{program_id}/checkout")
async def checkout_program(program_id: int, tier: str = "standard", user=Depends(get_current_user)):
    if tier not in ("standard", "premium"):
        tier = "standard"
    return await program_service.create_program_checkout(program_id, user["sub"], tier)  # type: ignore[index]
