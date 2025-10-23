"""Winter Arc Post Suggestions Service - Trigger logic for community engagement prompts."""
from datetime import UTC, datetime

from app.infra.supabase.client import supabase


async def create_suggestion(
    user_id: str,
    program_id: int,
    suggestion_type: str,
    title: str,
    message: str,
    metadata: dict | None = None,
):
    """Create a new post suggestion for a user."""
    if supabase is None:
        return None

    data = {
        "user_id": user_id,
        "program_id": program_id,
        "suggestion_type": suggestion_type,
        "title": title,
        "message": message,
        "triggered_at": datetime.now(UTC).isoformat(),
        "is_dismissed": False,
        "is_posted": False,
    }

    if metadata:
        data["metadata"] = metadata

    res = supabase.table("winter_arc_post_suggestions").insert(data).execute()
    result_data = res.data if hasattr(res, "data") else res
    return result_data[0] if result_data else None


async def get_active_suggestions(user_id: str, program_id: int):
    """Get all active (not dismissed, not posted) suggestions for a user."""
    if supabase is None:
        return []

    res = (
        supabase.table("winter_arc_post_suggestions")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .eq("is_dismissed", False)
        .eq("is_posted", False)
        .order("triggered_at", desc=True)
        .execute()
    )
    return res.data if hasattr(res, "data") else res


async def dismiss_suggestion(suggestion_id: int):
    """Mark a suggestion as dismissed."""
    if supabase is None:
        return None

    res = (
        supabase.table("winter_arc_post_suggestions")
        .update({"is_dismissed": True})
        .eq("id", suggestion_id)
        .execute()
    )
    result_data = res.data if hasattr(res, "data") else res
    return result_data[0] if result_data else None


async def mark_suggestion_posted(suggestion_id: int):
    """Mark a suggestion as posted."""
    if supabase is None:
        return None

    res = (
        supabase.table("winter_arc_post_suggestions")
        .update({"is_posted": True})
        .eq("id", suggestion_id)
        .execute()
    )
    result_data = res.data if hasattr(res, "data") else res
    return result_data[0] if result_data else None


async def check_and_trigger_suggestions(user_id: str, program_id: int):
    """
    Check user's progress and trigger appropriate post suggestions.

    Suggestion types:
    - milestone_streak: Daily/weekly streak milestones (7, 14, 30 days)
    - achievement_unlocked: New achievement earned
    - weight_progress: Significant weight change (5% or more)
    - weekly_completion: Completed all weekly tasks
    - perfect_week: 7 days completed in a row
    """
    if supabase is None:
        return []

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
        return []

    progress = progress_data[0]

    # Get existing suggestions to avoid duplicates
    existing = await get_active_suggestions(user_id, program_id)
    existing_types = {s["suggestion_type"] for s in existing}

    triggered = []

    # Check for streak milestones
    daily_streak = progress.get("current_daily_streak", 0)
    if daily_streak == 7 and "streak_7" not in existing_types:
        suggestion = await create_suggestion(
            user_id,
            program_id,
            "streak_7",
            "7-Day Streak!",
            "You've completed 7 days in a row! Share your progress and inspire others in the community.",
            {"streak_days": 7},
        )
        if suggestion:
            triggered.append(suggestion)

    if daily_streak == 14 and "streak_14" not in existing_types:
        suggestion = await create_suggestion(
            user_id,
            program_id,
            "streak_14",
            "2-Week Warrior!",
            "14 days of consistency! Your discipline is showing. Share what's working for you.",
            {"streak_days": 14},
        )
        if suggestion:
            triggered.append(suggestion)

    if daily_streak == 30 and "streak_30" not in existing_types:
        suggestion = await create_suggestion(
            user_id,
            program_id,
            "streak_30",
            "30-Day Champion!",
            "A full month of dedication! Share your transformation story with the community.",
            {"streak_days": 30},
        )
        if suggestion:
            triggered.append(suggestion)

    # Check for weekly streak milestones
    weekly_streak = progress.get("current_weekly_streak", 0)
    if weekly_streak == 4 and "weekly_streak_4" not in existing_types:
        suggestion = await create_suggestion(
            user_id,
            program_id,
            "weekly_streak_4",
            "Monthly Momentum!",
            "4 perfect weeks! You're in the zone. Share your weekly routine with others.",
            {"streak_weeks": 4},
        )
        if suggestion:
            triggered.append(suggestion)

    # Check for weight progress (if tracked)
    current_weight = progress.get("current_weight_kg")
    if current_weight:
        # Get first snapshot to compare
        snapshots_res = (
            supabase.table("winter_arc_progress_snapshots")
            .select("weight_kg")
            .eq("user_id", user_id)
            .eq("program_id", program_id)
            .order("snapshot_date", desc=False)
            .limit(1)
            .execute()
        )
        snapshots = (
            snapshots_res.data if hasattr(snapshots_res, "data") else snapshots_res
        )

        if snapshots and len(snapshots) > 0:
            first_weight = snapshots[0]["weight_kg"]
            weight_change_pct = abs(
                (current_weight - first_weight) / first_weight * 100
            )

            if weight_change_pct >= 5 and "weight_milestone_5" not in existing_types:
                suggestion = await create_suggestion(
                    user_id,
                    program_id,
                    "weight_milestone_5",
                    "Major Progress!",
                    f"You've achieved a {weight_change_pct:.1f}% change! Share your journey with the community.",
                    {
                        "weight_change_pct": round(weight_change_pct, 1),
                        "first_weight": first_weight,
                        "current_weight": current_weight,
                    },
                )
                if suggestion:
                    triggered.append(suggestion)

    # Check for achievement unlocks (recent)
    achievements_res = (
        supabase.table("winter_arc_user_achievements")
        .select("achievement:achievement_id(*)")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .order("unlocked_at", desc=True)
        .limit(1)
        .execute()
    )
    recent_achievements = (
        achievements_res.data if hasattr(achievements_res, "data") else achievements_res
    )

    if recent_achievements and len(recent_achievements) > 0:
        achievement = recent_achievements[0].get("achievement", {})
        achievement_code = achievement.get("code")
        suggestion_type = f"achievement_{achievement_code}"

        if suggestion_type not in existing_types:
            suggestion = await create_suggestion(
                user_id,
                program_id,
                suggestion_type,
                f"Achievement Unlocked: {achievement.get('name', 'Achievement')}",
                f"You just earned {achievement.get('name')}! Share your accomplishment.",
                {"achievement_code": achievement_code},
            )
            if suggestion:
                triggered.append(suggestion)

    return triggered
