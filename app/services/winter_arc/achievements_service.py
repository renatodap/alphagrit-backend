"""Winter Arc Achievements Service - Badge unlocking and management."""
from datetime import UTC, datetime

from app.infra.supabase.client import supabase


async def get_all_achievements():
    """Get all available achievements."""
    if supabase is None:
        return []

    res = supabase.table("winter_arc_achievements").select("*").execute()
    return res.data if hasattr(res, "data") else res


async def get_user_achievements(user_id: str, program_id: int):
    """Get all achievements unlocked by a user for a program."""
    if supabase is None:
        return []

    res = (
        supabase.table("winter_arc_user_achievements")
        .select("*, achievement:achievement_id(*)")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .order("unlocked_at", desc=True)
        .execute()
    )
    return res.data if hasattr(res, "data") else res


async def unlock_achievement(user_id: str, program_id: int, achievement_id: int):
    """Unlock an achievement for a user (idempotent - won't duplicate)."""
    if supabase is None:
        return None

    # Check if already unlocked
    existing = (
        supabase.table("winter_arc_user_achievements")
        .select("id")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .eq("achievement_id", achievement_id)
        .limit(1)
        .execute()
    )
    already_unlocked = bool(
        (existing.data if hasattr(existing, "data") else existing) or []
    )

    if already_unlocked:
        return {"already_unlocked": True}

    # Insert new achievement
    data = {
        "user_id": user_id,
        "program_id": program_id,
        "achievement_id": achievement_id,
        "unlocked_at": datetime.now(UTC).isoformat(),
    }

    res = supabase.table("winter_arc_user_achievements").insert(data).execute()
    result_data = res.data if hasattr(res, "data") else res
    return result_data[0] if result_data else None


async def check_and_unlock_achievements(user_id: str, program_id: int):
    """Check user's progress and unlock any achievements they've earned."""
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
    newly_unlocked = []

    # Define achievement criteria (these IDs should match database)
    # Note: You'll need to insert these achievements into the database first

    criteria = [
        # Streak achievements
        {
            "code": "FIRST_DAY",
            "check": lambda p: p.get("current_daily_streak", 0) >= 1,
        },
        {
            "code": "WEEK_WARRIOR",
            "check": lambda p: p.get("current_daily_streak", 0) >= 7,
        },
        {
            "code": "FORTNIGHT_FORCE",
            "check": lambda p: p.get("current_daily_streak", 0) >= 14,
        },
        {
            "code": "MONTH_MASTER",
            "check": lambda p: p.get("current_daily_streak", 0) >= 30,
        },
        {
            "code": "PERFECT_WEEK",
            "check": lambda p: p.get("current_weekly_streak", 0) >= 1,
        },
        {
            "code": "MONTHLY_MOMENTUM",
            "check": lambda p: p.get("current_weekly_streak", 0) >= 4,
        },
        # Timer achievements
        {
            "code": "SILENCE_SEEKER",
            "check": lambda p: p.get("three_min_timer_completions", 0) >= 10,
        },
        {
            "code": "MEDITATION_MASTER",
            "check": lambda p: p.get("three_min_timer_completions", 0) >= 50,
        },
        # Total completion achievements
        {
            "code": "CONSISTENCY_KING",
            "check": lambda p: p.get("total_days_completed", 0) >= 30,
        },
        {
            "code": "WINTER_WARRIOR",
            "check": lambda p: p.get("total_days_completed", 0) >= 84,
        },  # 12 weeks
    ]

    # Get all achievements from database to match codes to IDs
    all_achievements = await get_all_achievements()
    achievement_map = {a["code"]: a["id"] for a in all_achievements}

    # Check each criterion
    for criterion in criteria:
        code = criterion["code"]
        if code in achievement_map and criterion["check"](progress):
            achievement_id = achievement_map[code]
            result = await unlock_achievement(user_id, program_id, achievement_id)
            if result and not result.get("already_unlocked"):
                newly_unlocked.append(result)

    return newly_unlocked


async def get_achievement_progress(user_id: str, program_id: int):
    """Get user's progress toward each achievement."""
    if supabase is None:
        return []

    # Get all achievements
    all_achievements = await get_all_achievements()

    # Get user's unlocked achievements
    unlocked = await get_user_achievements(user_id, program_id)
    unlocked_ids = {ua["achievement_id"] for ua in unlocked}

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
    progress = progress_data[0] if progress_data else {}

    # Build progress report
    achievement_progress = []
    for achievement in all_achievements:
        code = achievement["code"]
        unlocked = achievement["id"] in unlocked_ids

        # Calculate progress percentage based on code
        current = 0
        target = 100
        percentage = 0

        if code == "FIRST_DAY":
            target = 1
            current = min(progress.get("current_daily_streak", 0), target)
        elif code == "WEEK_WARRIOR":
            target = 7
            current = min(progress.get("current_daily_streak", 0), target)
        elif code == "FORTNIGHT_FORCE":
            target = 14
            current = min(progress.get("current_daily_streak", 0), target)
        elif code == "MONTH_MASTER":
            target = 30
            current = min(progress.get("current_daily_streak", 0), target)
        elif code == "PERFECT_WEEK":
            target = 1
            current = min(progress.get("current_weekly_streak", 0), target)
        elif code == "MONTHLY_MOMENTUM":
            target = 4
            current = min(progress.get("current_weekly_streak", 0), target)
        elif code == "SILENCE_SEEKER":
            target = 10
            current = min(progress.get("three_min_timer_completions", 0), target)
        elif code == "MEDITATION_MASTER":
            target = 50
            current = min(progress.get("three_min_timer_completions", 0), target)
        elif code == "CONSISTENCY_KING":
            target = 30
            current = min(progress.get("total_days_completed", 0), target)
        elif code == "WINTER_WARRIOR":
            target = 84
            current = min(progress.get("total_days_completed", 0), target)

        if target > 0:
            percentage = int((current / target) * 100)

        achievement_progress.append(
            {
                "achievement": achievement,
                "unlocked": unlocked,
                "current": current,
                "target": target,
                "percentage": percentage,
            }
        )

    return achievement_progress
