import re
import uuid
from pathlib import Path


_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_filename(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return f"{uuid.uuid4().hex}.bin"
    # keep only safe characters
    safe = _SAFE.sub("-", name)
    # prevent leading dots
    safe = safe.lstrip(".")
    # ensure we have at least a basename
    if not safe:
        safe = uuid.uuid4().hex
    return safe[:128]


def _with_ext(name: str, fallback_ext: str = ".jpg") -> str:
    p = Path(name)
    if p.suffix:
        return sanitize_filename(name)
    return sanitize_filename(p.stem + fallback_ext)


def post_photo_key(program_id: int, user_id: str, post_id: int, filename: str) -> str:
    fname = _with_ext(filename, ".jpg")
    return f"program_{program_id}/user_{user_id}/post_{post_id}/{fname}"


def metric_photo_key(user_id: str, metric_id: int, filename: str) -> str:
    fname = _with_ext(filename, ".jpg")
    return f"user_{user_id}/metric_{metric_id}/{fname}"

