"""Winter Arc Progress Service - User progress tracking, snapshots, and macro calculations."""
from datetime import UTC, datetime

from app.infra.supabase.client import supabase


async def get_user_progress(user_id: str, program_id: int):
    """Get user's Winter Arc progress for a specific program."""
    if supabase is None:
        return None

    res = (
        supabase.table("winter_arc_user_progress")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .limit(1)
        .execute()
    )
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else None


async def create_or_update_progress(
    user_id: str,
    program_id: int,
    mission_statement: str | None = None,
    current_weight_kg: float | None = None,
    height_cm: float | None = None,
    age: int | None = None,
    gender: str | None = None,
    activity_level: str | None = None,
    goal: str | None = None,
    bmr: float | None = None,
    tdee: float | None = None,
    target_calories: float | None = None,
    protein_g: float | None = None,
    carbs_g: float | None = None,
    fat_g: float | None = None,
    show_on_leaderboard: bool | None = None,
):
    """Create or update user progress record."""
    if supabase is None:
        return None

    # Check if record exists
    existing = await get_user_progress(user_id, program_id)

    data = {}
    if mission_statement is not None:
        data["mission_statement"] = mission_statement
    if current_weight_kg is not None:
        data["current_weight_kg"] = current_weight_kg
    if height_cm is not None:
        data["height_cm"] = height_cm
    if age is not None:
        data["age"] = age
    if gender is not None:
        data["gender"] = gender
    if activity_level is not None:
        data["activity_level"] = activity_level
    if goal is not None:
        data["goal"] = goal
    if bmr is not None:
        data["bmr"] = bmr
    if tdee is not None:
        data["tdee"] = tdee
    if target_calories is not None:
        data["target_calories"] = target_calories
    if protein_g is not None:
        data["protein_g"] = protein_g
    if carbs_g is not None:
        data["carbs_g"] = carbs_g
    if fat_g is not None:
        data["fat_g"] = fat_g
    if show_on_leaderboard is not None:
        data["show_on_leaderboard"] = show_on_leaderboard

    if existing:
        # Update existing record
        res = (
            supabase.table("winter_arc_user_progress")
            .update(data)
            .eq("user_id", user_id)
            .eq("program_id", program_id)
            .execute()
        )
    else:
        # Create new record
        data["user_id"] = user_id
        data["program_id"] = program_id
        res = supabase.table("winter_arc_user_progress").insert(data).execute()

    result_data = res.data if hasattr(res, "data") else res
    return result_data[0] if result_data else None


async def increment_timer_completions(user_id: str, program_id: int, minutes: int = 3):
    """Increment timer completion count and total minutes."""
    if supabase is None:
        return None

    # Ensure progress record exists
    progress = await get_user_progress(user_id, program_id)
    if not progress:
        progress = await create_or_update_progress(user_id, program_id)

    # Increment counters using SQL
    res = (
        supabase.rpc(
            "increment_timer_stats",
            {"p_user_id": user_id, "p_program_id": program_id, "p_minutes": minutes},
        )
        .execute()
    )

    # If RPC doesn't exist, fallback to manual update
    if not res or (hasattr(res, "data") and not res.data):
        current_completions = progress.get("three_min_timer_completions", 0)
        current_minutes = progress.get("total_timer_minutes", 0)
        return await create_or_update_progress(
            user_id,
            program_id,
            **{
                "three_min_timer_completions": current_completions + 1,
                "total_timer_minutes": current_minutes + minutes,
            },
        )

    return res.data if hasattr(res, "data") else res


async def create_progress_snapshot(
    user_id: str, program_id: int, weight_kg: float, notes: str | None = None
):
    """Create a progress snapshot for tracking weight over time."""
    if supabase is None:
        return None

    data = {
        "user_id": user_id,
        "program_id": program_id,
        "weight_kg": weight_kg,
        "snapshot_date": datetime.now(UTC).isoformat(),
    }
    if notes:
        data["notes"] = notes

    res = supabase.table("winter_arc_progress_snapshots").insert(data).execute()
    result_data = res.data if hasattr(res, "data") else res
    return result_data[0] if result_data else None


async def get_progress_snapshots(user_id: str, program_id: int, limit: int = 50):
    """Get user's progress snapshots ordered by date."""
    if supabase is None:
        return []

    res = (
        supabase.table("winter_arc_progress_snapshots")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .order("snapshot_date", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data if hasattr(res, "data") else res


async def update_leaderboard_visibility(
    user_id: str, program_id: int, show_on_leaderboard: bool
):
    """Update user's leaderboard visibility preference."""
    return await create_or_update_progress(
        user_id, program_id, show_on_leaderboard=show_on_leaderboard
    )
