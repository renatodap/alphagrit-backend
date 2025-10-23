from fastapi import Header, HTTPException, Depends
from app.core.auth import verifier
from app.infra.supabase.client import get_supabase


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


# ============================================================================
# Winter Arc Access Control
# ============================================================================


# Admin user IDs (Wagner + Renato) - bypass all access checks
ADMIN_USER_IDS = [
    # TODO: Replace with actual user IDs from Supabase Auth
    # Get these from: SELECT id, email FROM auth.users WHERE email IN ('wagner@email.com', 'renato@email.com');
    # Example format: "550e8400-e29b-41d4-a716-446655440000"
]


async def has_ebook_access(user_id: str, program_id: int) -> bool:
    """
    Check if user has purchased ebook access (any tier).

    Returns True if:
    - User purchased ebook_only, community_standard, or community_premium
    - OR user is Wagner or Renato (admin bypass)
    """
    # Admin bypass
    if user_id in ADMIN_USER_IDS:
        return True

    supabase = get_supabase()
    if supabase is None:
        return False

    try:
        res = (
            supabase.table("user_programs")
            .select("product_type")
            .eq("user_id", user_id)
            .eq("program_id", program_id)
            .in_("product_type", ["ebook_only", "community_standard", "community_premium"])
            .limit(1)
            .execute()
        )
        data = res.data if hasattr(res, "data") else res
        return len(data) > 0
    except Exception:
        return False


async def has_community_access(user_id: str, program_id: int) -> bool:
    """
    Check if user has purchased community access (standard or premium tier).

    Returns True if:
    - User purchased community_standard or community_premium
    - OR user is Wagner or Renato (admin bypass)

    Note: ebook_only purchases do NOT grant community access
    """
    # Admin bypass
    if user_id in ADMIN_USER_IDS:
        return True

    supabase = get_supabase()
    if supabase is None:
        return False

    try:
        res = (
            supabase.table("user_programs")
            .select("product_type")
            .eq("user_id", user_id)
            .eq("program_id", program_id)
            .in_("product_type", ["community_standard", "community_premium"])
            .limit(1)
            .execute()
        )
        data = res.data if hasattr(res, "data") else res
        return len(data) > 0
    except Exception:
        return False


async def is_premium_tier(user_id: str, program_id: int) -> bool:
    """
    Check if user has premium tier (Wagner-guaranteed responses).

    Returns True if:
    - User purchased community_premium
    - OR user is Wagner or Renato (admin bypass)
    """
    # Admin bypass
    if user_id in ADMIN_USER_IDS:
        return True

    supabase = get_supabase()
    if supabase is None:
        return False

    try:
        res = (
            supabase.table("user_programs")
            .select("tier, product_type")
            .eq("user_id", user_id)
            .eq("program_id", program_id)
            .eq("product_type", "community_premium")
            .eq("tier", "premium")
            .limit(1)
            .execute()
        )
        data = res.data if hasattr(res, "data") else res
        return len(data) > 0
    except Exception:
        return False


async def require_ebook_access(program_id: int, user=Depends(get_current_user)):
    """
    Dependency that requires ebook access.
    Raises 403 if user doesn't have access.
    """
    user_id = user.get("sub") or user.get("id")
    if not await has_ebook_access(user_id, program_id):
        raise HTTPException(
            status_code=403,
            detail="ebook_access_required",
        )
    return user


async def require_community_access(program_id: int, user=Depends(get_current_user)):
    """
    Dependency that requires community access.
    Raises 403 if user doesn't have access.
    """
    user_id = user.get("sub") or user.get("id")
    if not await has_community_access(user_id, program_id):
        raise HTTPException(
            status_code=403,
            detail="community_access_required",
        )
    return user
