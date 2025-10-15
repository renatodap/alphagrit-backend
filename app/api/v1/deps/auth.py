from fastapi import Header, HTTPException
from fastapi import HTTPException
from app.core.auth import verifier


async def get_current_user(authorization: str = Header(...)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = authorization.split(" ", 1)[1]
    try:
        payload = await verifier.verify(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token")


async def get_lang(accept_language: str | None = Header(None)) -> str:
    # very simple language picker
    if accept_language and accept_language.lower().startswith("pt"):
        return "pt"
    return "en"
