"""Winter Arc Leaderboard Service - Score calculation and rankings."""
from app.infra.supabase.client import supabase


async def calculate_leaderboard_score(user_id: str, program_id: int) -> float:
    """
    Calculate leaderboard score for a user.

    Scoring formula:
    - Daily streak: current_daily_streak * 10 points
    - Weekly streak: current_weekly_streak * 50 points
    - Total days completed: total_days_completed * 5 points
    - Total weeks completed: total_weeks_completed * 25 points
    - Achievements: number of achievements * 100 points
    """
    if supabase is None:
        return 0.0

    # Get user progress
    progress_res = (
        supabase.table("winter_arc_user_progress")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .limit(1)
        .execute()
    )
    progress_data = progress_res.data if hasattr(progress_res, "data") else progress_res
    if not progress_data:
        return 0.0

    progress = progress_data[0]

    # Get achievement count
    achievements_res = (
        supabase.table("winter_arc_user_achievements")
        .select("id")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .execute()
    )
    achievements_data = (
        achievements_res.data if hasattr(achievements_res, "data") else achievements_res
    )
    achievement_count = len(achievements_data) if achievements_data else 0

    # Calculate score
    score = 0.0
    score += progress.get("current_daily_streak", 0) * 10
    score += progress.get("current_weekly_streak", 0) * 50
    score += progress.get("total_days_completed", 0) * 5
    score += progress.get("total_weeks_completed", 0) * 25
    score += achievement_count * 100

    return score


async def update_user_leaderboard_score(user_id: str, program_id: int):
    """Recalculate and update user's leaderboard score."""
    if supabase is None:
        return None

    score = await calculate_leaderboard_score(user_id, program_id)

    # Update score in progress table
    res = (
        supabase.table("winter_arc_user_progress")
        .update({"leaderboard_score": score})
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .execute()
    )

    result_data = res.data if hasattr(res, "data") else res
    return result_data[0] if result_data else None


async def get_leaderboard(program_id: int, limit: int = 100, offset: int = 0):
    """
    Get the leaderboard for a program.
    Only includes users who have opted in (show_on_leaderboard = true).
    """
    if supabase is None:
        return []

    res = (
        supabase.table("winter_arc_leaderboard_view")
        .select("*")
        .eq("program_id", program_id)
        .eq("show_on_leaderboard", True)
        .order("leaderboard_rank", desc=False)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return res.data if hasattr(res, "data") else res


async def get_user_leaderboard_position(user_id: str, program_id: int):
    """Get a user's position on the leaderboard."""
    if supabase is None:
        return None

    # First update their score
    await update_user_leaderboard_score(user_id, program_id)

    # Get their rank from the view
    res = (
        supabase.table("winter_arc_leaderboard_view")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .limit(1)
        .execute()
    )

    data = res.data if hasattr(res, "data") else res
    return data[0] if data else None


async def get_leaderboard_context(
    user_id: str, program_id: int, context_size: int = 5
):
    """
    Get leaderboard entries around a user's position.
    Returns entries above and below the user for context.
    """
    if supabase is None:
        return {"user_entry": None, "entries_above": [], "entries_below": []}

    # Get user's position
    user_entry = await get_user_leaderboard_position(user_id, program_id)
    if not user_entry:
        return {"user_entry": None, "entries_above": [], "entries_below": []}

    user_rank = user_entry.get("leaderboard_rank")
    if user_rank is None:
        return {"user_entry": user_entry, "entries_above": [], "entries_below": []}

    # Get entries above (lower rank numbers)
    above_start = max(1, user_rank - context_size)
    above_end = user_rank - 1

    entries_above = []
    if above_end >= above_start:
        res_above = (
            supabase.table("winter_arc_leaderboard_view")
            .select("*")
            .eq("program_id", program_id)
            .eq("show_on_leaderboard", True)
            .gte("leaderboard_rank", above_start)
            .lte("leaderboard_rank", above_end)
            .order("leaderboard_rank", desc=False)
            .execute()
        )
        entries_above = (
            res_above.data if hasattr(res_above, "data") else res_above
        ) or []

    # Get entries below (higher rank numbers)
    below_start = user_rank + 1
    below_end = user_rank + context_size

    res_below = (
        supabase.table("winter_arc_leaderboard_view")
        .select("*")
        .eq("program_id", program_id)
        .eq("show_on_leaderboard", True)
        .gte("leaderboard_rank", below_start)
        .lte("leaderboard_rank", below_end)
        .order("leaderboard_rank", desc=False)
        .execute()
    )
    entries_below = (res_below.data if hasattr(res_below, "data") else res_below) or []

    return {
        "user_entry": user_entry,
        "entries_above": entries_above,
        "entries_below": entries_below,
    }


async def update_all_leaderboard_scores(program_id: int):
    """
    Recalculate scores for all users in a program.
    This can be run periodically or triggered manually.
    """
    if supabase is None:
        return {"updated": 0}

    # Get all users in the program
    res = (
        supabase.table("winter_arc_user_progress")
        .select("user_id")
        .eq("program_id", program_id)
        .execute()
    )
    users = res.data if hasattr(res, "data") else res

    updated_count = 0
    for user in users:
        user_id = user["user_id"]
        await update_user_leaderboard_score(user_id, program_id)
        updated_count += 1

    return {"updated": updated_count}
