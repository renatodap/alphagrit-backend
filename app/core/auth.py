import time
from typing import Any, Dict, Optional

import httpx
from jose import jwt

from app.core.logging import get_logger
from app.core.config import settings


log = get_logger(__name__)


class JWKSCache:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl = ttl_seconds
        self._keys: Optional[Dict[str, Any]] = None
        self._expires_at: float = 0.0

    async def get(self, url: str) -> Dict[str, Any]:
        now = time.time()
        if self._keys and now < self._expires_at:
            return self._keys
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            self._keys = data
            self._expires_at = now + self.ttl
            return data


class SupabaseJWTVerifier:
    def __init__(self) -> None:
        # Build JWKS URL from SUPABASE_URL if not provided
        base = settings.supabase_url.rstrip("/") if settings.supabase_url else ""
        self.jwks_url = (
            settings.supabase_jwks_url
            or (f"{base}/auth/v1/.well-known/jwks.json" if base else None)
        )
        self.issuer = settings.supabase_jwt_issuer or (f"{base}/auth/v1" if base else None)
        self.audience = settings.supabase_jwt_audience or None
        self.cache = JWKSCache()

    async def verify(self, token: str) -> dict:
        if not self.jwks_url:
            # Fallback: accept unverified in dev if no URL configured
            log.warning("JWKS URL not configured; falling back to unverified claims")
            return jwt.get_unverified_claims(token)

        keys = await self.cache.get(self.jwks_url)
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        key = None
        for jwk in keys.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        if key is None and keys.get("keys"):
            # Try first key if kid missing
            key = keys["keys"][0]

        options = {"verify_aud": bool(self.audience), "verify_at_hash": False}

        return jwt.decode(
            token,
            key,
            algorithms=["RS256", "HS256"],
            audience=self.audience,
            issuer=self.issuer,
            options=options,
        )


verifier = SupabaseJWTVerifier()

