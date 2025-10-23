from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.deps.auth import get_current_user
from app.services.admin import admin_service

router = APIRouter()


def require_admin(user):
    if "admin" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/analytics/sales")
async def analytics_sales(user=Depends(get_current_user)):
    require_admin(user)
    return await admin_service.analytics_sales()


@router.get("/analytics/programs")
async def analytics_programs(user=Depends(get_current_user)):
    require_admin(user)
    return await admin_service.analytics_programs()


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, user=Depends(get_current_user)):
    require_admin(user)
    return await admin_service.delete_post(post_id)


# ============================================================================
# Winter Arc Premium Posts Management
# ============================================================================


class MarkRespondedRequest(BaseModel):
    notes: str | None = None


@router.get("/winter-arc/premium-posts")
async def get_premium_posts_queue(program_id: int = 1, user=Depends(get_current_user)):
    """
    Get premium posts queue for Wagner admin view.

    Returns posts from premium tier users, with unresponded posts first.
    Each post includes:
    - Post details (id, title, content, posted_at)
    - User details (user_id, user_name, user_avatar)
    - Response status (has_response, responded_at, responded_by, notes)

    Query params:
    - program_id: Program ID (default 1 for Winter Arc)
    """
    require_admin(user)
    return await admin_service.get_premium_posts_queue(program_id)


@router.post("/winter-arc/posts/{post_id}/mark-responded")
async def mark_post_responded(
    post_id: int, request: MarkRespondedRequest, user=Depends(get_current_user)
):
    """
    Mark a premium post as responded to by Wagner.

    Body:
    - notes (optional): Internal notes about the response

    This endpoint records when Wagner (or admin) has responded to a premium user's post,
    fulfilling the Wagner-guaranteed response promise.
    """
    require_admin(user)
    user_id = user.get("sub") or user.get("id")
    return await admin_service.mark_post_responded(post_id, user_id, request.notes)


@router.get("/winter-arc/premium-stats")
async def get_premium_stats(program_id: int = 1, user=Depends(get_current_user)):
    """
    Get statistics about premium posts for admin dashboard.

    Returns:
    - total_premium_users: Number of users with premium tier
    - total_premium_posts: Total posts from premium users
    - unresponded_posts: Number of posts still needing response
    - avg_response_time_hours: Average time to respond (hours)

    Query params:
    - program_id: Program ID (default 1 for Winter Arc)
    """
    require_admin(user)
    return await admin_service.get_premium_stats(program_id)
