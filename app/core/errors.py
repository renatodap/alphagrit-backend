from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status
from fastapi import HTTPException
from app.api.v1.deps.auth import get_lang
from app.shared.i18n.localize import t


def error_envelope(code: str, message: str, details: dict | None = None) -> dict:
    err = {"error": {"code": code, "message": message}}
    if details:
        err["error"]["details"] = details
    return err


def init_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        lang = await get_lang(request.headers.get("accept-language"))  # type: ignore[arg-type]
        code = "UNKNOWN"
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            # if detail carries a string code like 'invalid_token', prefer it
            code = "INVALID_TOKEN" if str(exc.detail).lower() == "invalid_token" else "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "FORBIDDEN"
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:
            code = "BAD_REQUEST"
        key = {
            "UNAUTHORIZED": "errors.unauthorized",
            "INVALID_TOKEN": "errors.invalid_token",
            "FORBIDDEN": "errors.forbidden",
            "NOT_FOUND": "errors.not_found",
            "BAD_REQUEST": "errors.bad_request",
        }.get(code, "errors.unauthorized")
        message = t(lang, key)
        return JSONResponse(status_code=exc.status_code, content=error_envelope(code, message))

    @app.exception_handler(Exception)
    async def default_exception_handler(request: Request, exc: Exception):
        lang = await get_lang(request.headers.get("accept-language"))  # type: ignore[arg-type]
        message = t(lang, "errors.not_found") if "not found" in str(exc).lower() else str(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_envelope("INTERNAL_ERROR", message or "Internal server error"),
        )
