from app.infra.supabase.client import supabase
from datetime import datetime


async def analytics_sales():
    if supabase is None:
        return {"total_revenue_cents": 0, "paid_orders": 0}
    paid = supabase.table("purchases").select("price_cents,status").eq("status", "paid").execute()
    rows = paid.data if hasattr(paid, "data") else paid
    total = sum(r.get("price_cents", 0) for r in rows or [])
    return {"total_revenue_cents": total, "paid_orders": len(rows or [])}


async def analytics_programs():
    if supabase is None:
        return {"memberships": 0}
    res = supabase.table("user_programs").select("id").execute()
    rows = res.data if hasattr(res, "data") else res
    return {"memberships": len(rows or [])}


async def delete_post(post_id: int):
    if supabase is None:
        return {"id": post_id, "deleted": True}
    res = supabase.table("posts").delete().eq("id", post_id).execute()
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else {"id": post_id, "deleted": True}


# ============================================================================
# Winter Arc Premium Posts Management
# ============================================================================


async def get_premium_posts_queue(program_id: int):
    """
    Get premium posts queue for Wagner admin view.
    Returns posts from premium tier users, with unresponded posts first.

    Returns:
    - post_id, user_id, user_name, user_avatar
    - title, content, posted_at
    - has_response, responded_at, responded_by, notes
    """
    if supabase is None:
        return []

    try:
        # Use the view created in migration 0009
        res = (
            supabase.from_("winter_arc_premium_posts_queue")
            .select("*")
            .eq("program_id", program_id)
            .execute()
        )
        data = res.data if hasattr(res, "data") else res
        return data or []
    except Exception:
        # Fallback: manual query if view doesn't exist yet
        try:
            # Get all premium users
            premium_users_res = (
                supabase.table("user_programs")
                .select("user_id")
                .eq("program_id", program_id)
                .eq("tier", "premium")
                .execute()
            )
            premium_users_data = (
                premium_users_res.data
                if hasattr(premium_users_res, "data")
                else premium_users_res
            )
            premium_user_ids = [u["user_id"] for u in (premium_users_data or [])]

            if not premium_user_ids:
                return []

            # Get their posts
            posts_res = (
                supabase.table("posts")
                .select(
                    """
                    id,
                    user_id,
                    title,
                    content,
                    created_at,
                    users!inner(full_name, avatar_url)
                """
                )
                .eq("program_id", program_id)
                .in_("user_id", premium_user_ids)
                .order("created_at", desc=True)
                .execute()
            )
            posts_data = posts_res.data if hasattr(posts_res, "data") else posts_res

            # Get responses
            responses_res = (
                supabase.table("winter_arc_premium_responses")
                .select("post_id, responded_at, responded_by, notes")
                .execute()
            )
            responses_data = (
                responses_res.data
                if hasattr(responses_res, "data")
                else responses_res
            )
            responses_by_post = {r["post_id"]: r for r in (responses_data or [])}

            # Combine data
            result = []
            for post in posts_data or []:
                response = responses_by_post.get(post["id"])
                result.append(
                    {
                        "post_id": post["id"],
                        "user_id": post["user_id"],
                        "user_name": post.get("users", {}).get("full_name", "Unknown"),
                        "user_avatar": post.get("users", {}).get("avatar_url"),
                        "title": post.get("title"),
                        "content": post.get("content"),
                        "posted_at": post.get("created_at"),
                        "has_response": response is not None,
                        "responded_at": response.get("responded_at") if response else None,
                        "responded_by": response.get("responded_by") if response else None,
                        "notes": response.get("notes") if response else None,
                    }
                )

            # Sort: unresponded first
            result.sort(key=lambda x: (x["has_response"], x["posted_at"]), reverse=True)
            return result
        except Exception:
            return []


async def mark_post_responded(post_id: int, responded_by: str, notes: str | None = None):
    """
    Mark a premium post as responded to by Wagner (or admin).

    Args:
    - post_id: ID of the post
    - responded_by: User ID of admin who responded
    - notes: Optional internal notes about the response
    """
    if supabase is None:
        return {"post_id": post_id, "responded": True}

    try:
        # Insert or update response record
        res = (
            supabase.table("winter_arc_premium_responses")
            .upsert(
                {
                    "post_id": post_id,
                    "responded_by": responded_by,
                    "responded_at": datetime.utcnow().isoformat(),
                    "notes": notes,
                },
                on_conflict="post_id",
            )
            .execute()
        )
        data = res.data if hasattr(res, "data") else res
        return data[0] if data else {"post_id": post_id, "responded": True}
    except Exception as e:
        raise Exception(f"Failed to mark post as responded: {str(e)}")


async def get_premium_stats(program_id: int):
    """
    Get stats about premium posts for admin dashboard.

    Returns:
    - total_premium_users
    - total_premium_posts
    - unresponded_posts
    - avg_response_time_hours
    """
    if supabase is None:
        return {
            "total_premium_users": 0,
            "total_premium_posts": 0,
            "unresponded_posts": 0,
            "avg_response_time_hours": 0,
        }

    try:
        # Count premium users
        premium_count_res = (
            supabase.table("user_programs")
            .select("id", count="exact")
            .eq("program_id", program_id)
            .eq("tier", "premium")
            .execute()
        )

        # Get posts queue
        posts = await get_premium_posts_queue(program_id)

        total_posts = len(posts)
        unresponded = sum(1 for p in posts if not p.get("has_response"))

        # Calculate avg response time (simplified)
        # TODO: Improve this calculation
        avg_response_time = 0

        return {
            "total_premium_users": premium_count_res.count if premium_count_res else 0,
            "total_premium_posts": total_posts,
            "unresponded_posts": unresponded,
            "avg_response_time_hours": avg_response_time,
        }
    except Exception:
        return {
            "total_premium_users": 0,
            "total_premium_posts": 0,
            "unresponded_posts": 0,
            "avg_response_time_hours": 0,
        }
