from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.api.v1.dto.waitlist_dto import WaitlistIn
from app.services.waitlist.waitlist_service import add_to_waitlist


router = APIRouter()


@router.post("")
async def join_waitlist(payload: WaitlistIn):
    res = await add_to_waitlist(payload.email, payload.language)
    if isinstance(res, dict) and res.get("duplicate"):
        raise HTTPException(status_code=409, detail="Email already registered")
    return JSONResponse(status_code=201, content=res)
