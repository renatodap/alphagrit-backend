from typing import Any, Optional

from app.infra.supabase.client import supabase
from app.shared.storage.constants import DEFAULT_UPLOAD_EXPIRES, METRICS_BUCKET, POST_BUCKET
from app.shared.storage.keys import metric_photo_key, post_photo_key, sanitize_filename


def _try_create_signed_upload_url(bucket: str, path: str, expires_in: int) -> Optional[str]:
    if supabase is None:
        return None
    try:
        # Some supabase-py versions may not support signed upload URLs.
        storage = supabase.storage.from_(bucket)
        create = getattr(storage, "create_signed_upload_url", None)
        if callable(create):
            res = create(path)
            # SDKs may return dict with 'signedUrl' or 'url'
            url = res.get("signedUrl") or res.get("url") if isinstance(res, dict) else None
            return url
        return None
    except Exception:
        return None


def _try_create_signed_download_url(bucket: str, path: str, expires_in: int) -> Optional[str]:
    if supabase is None:
        return None
    try:
        storage = supabase.storage.from_(bucket)
        res = storage.create_signed_url(path, expires_in)
        url = res.get("signedURL") or res.get("signedUrl") or res.get("url") if isinstance(res, dict) else None
        return url
    except Exception:
        return None


async def create_post_upload(user: dict, program_id: int, post_id: int, filename: str) -> dict[str, Any]:
    key = post_photo_key(program_id, user.get("sub"), post_id, sanitize_filename(filename))
    signed = _try_create_signed_upload_url(POST_BUCKET, key, DEFAULT_UPLOAD_EXPIRES)
    return {"bucket": POST_BUCKET, "path": key, "signed_url": signed}


async def create_metric_upload(user: dict, metric_id: int, filename: str) -> dict[str, Any]:
    key = metric_photo_key(user.get("sub"), metric_id, sanitize_filename(filename))
    signed = _try_create_signed_upload_url(METRICS_BUCKET, key, DEFAULT_UPLOAD_EXPIRES)
    return {"bucket": METRICS_BUCKET, "path": key, "signed_url": signed}


async def create_download_url(bucket: str, path: str, expires_in: int = DEFAULT_UPLOAD_EXPIRES) -> dict[str, Any]:
    signed = _try_create_signed_download_url(bucket, path, expires_in)
    return {"bucket": bucket, "path": path, "signed_url": signed}

