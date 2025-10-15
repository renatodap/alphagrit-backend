from fastapi import APIRouter, Depends

from app.api.v1.deps.auth import get_current_user
from app.services.users import profile_service
from app.api.v1.dto.profile_dto import ProfileUpdateIn

router = APIRouter()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return await profile_service.get_profile(user)


@router.put("/me")
async def update_me(payload: ProfileUpdateIn, user=Depends(get_current_user)):
    return await profile_service.update_profile(user, payload.model_dump(exclude_unset=True))
