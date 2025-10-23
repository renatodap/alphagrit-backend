"""Winter Arc Checklist Service - Daily and weekly checklist operations with streak tracking."""
from datetime import UTC, date, datetime, timedelta

from app.infra.supabase.client import supabase


def get_iso_week_info(target_date: date):
    """Get ISO year and week number for a given date."""
    iso_cal = target_date.isocalendar()
    return iso_cal[0], iso_cal[1]  # year, week_number


def get_week_start_end(year: int, week: int):
    """Get the start and end dates for an ISO week."""
    # Find the first day of the year
    jan_4 = date(year, 1, 4)
    week_1_start = jan_4 - timedelta(days=jan_4.weekday())
    target_week_start = week_1_start + timedelta(weeks=week - 1)
    target_week_end = target_week_start + timedelta(days=6)
    return target_week_start, target_week_end


# ===== DAILY CHECKLISTS =====


async def get_daily_checklist(user_id: str, program_id: int, checklist_date: date):
    """Get daily checklist for a specific date."""
    if supabase is None:
        return None

    res = (
        supabase.table("winter_arc_daily_checklists")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .eq("checklist_date", checklist_date.isoformat())
        .limit(1)
        .execute()
    )
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else None


async def get_daily_checklists_range(
    user_id: str, program_id: int, start_date: date, end_date: date
):
    """Get daily checklists for a date range."""
    if supabase is None:
        return []

    res = (
        supabase.table("winter_arc_daily_checklists")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .gte("checklist_date", start_date.isoformat())
        .lte("checklist_date", end_date.isoformat())
        .order("checklist_date", desc=False)
        .execute()
    )
    return res.data if hasattr(res, "data") else res


async def update_daily_checklist(
    user_id: str, program_id: int, checklist_date: date, updates: dict[str, bool]
):
    """Update or create daily checklist with completion data."""
    if supabase is None:
        return None

    # Check if checklist exists for this date
    existing = await get_daily_checklist(user_id, program_id, checklist_date)

    # Valid daily checklist fields
    valid_fields = {
        "wake_up_early",
        "ten_min_silence",
        "morning_hydration",
        "workout",
        "clean_eating",
        "review_mission",
        "small_sacrifice",
        "moment_silence",
        "act_of_honor",
        "small_overcoming",
    }

    # Filter to only valid fields
    data = {k: v for k, v in updates.items() if k in valid_fields}

    if existing:
        # Update existing checklist
        res = (
            supabase.table("winter_arc_daily_checklists")
            .update(data)
            .eq("user_id", user_id)
            .eq("program_id", program_id)
            .eq("checklist_date", checklist_date.isoformat())
            .execute()
        )
    else:
        # Create new checklist
        data["user_id"] = user_id
        data["program_id"] = program_id
        data["checklist_date"] = checklist_date.isoformat()
        res = supabase.table("winter_arc_daily_checklists").insert(data).execute()

    result_data = res.data if hasattr(res, "data") else res
    updated_checklist = result_data[0] if result_data else None

    # Update streaks if checklist was completed
    if updated_checklist and updated_checklist.get("is_fully_completed"):
        await update_daily_streak(user_id, program_id)

    return updated_checklist


async def update_daily_streak(user_id: str, program_id: int):
    """Recalculate and update daily streak based on completed checklists."""
    if supabase is None:
        return

    # Get all completed daily checklists ordered by date desc
    res = (
        supabase.table("winter_arc_daily_checklists")
        .select("checklist_date,is_fully_completed")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .eq("is_fully_completed", True)
        .order("checklist_date", desc=True)
        .execute()
    )
    completed = res.data if hasattr(res, "data") else res

    if not completed:
        # No completed checklists - reset streaks
        await _update_progress_streaks(user_id, program_id, 0, 0, None, None)
        return

    # Calculate current streak (consecutive days from today backwards)
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    yesterday = None

    for entry in completed:
        entry_date = (
            datetime.fromisoformat(entry["checklist_date"]).date()
            if isinstance(entry["checklist_date"], str)
            else entry["checklist_date"]
        )

        if yesterday is None:
            # First entry - check if it's today or yesterday
            today = datetime.now(UTC).date()
            if entry_date == today or entry_date == today - timedelta(days=1):
                current_streak = 1
                temp_streak = 1
                yesterday = entry_date
            else:
                # Streak broken
                temp_streak = 1
        else:
            # Check if consecutive
            if entry_date == yesterday - timedelta(days=1):
                temp_streak += 1
                if yesterday >= datetime.now(UTC).date() - timedelta(days=1):
                    current_streak = temp_streak
                yesterday = entry_date
            else:
                # Streak broken
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
                yesterday = entry_date

    longest_streak = max(longest_streak, temp_streak, current_streak)
    total_completed = len(completed)

    await _update_progress_streaks(
        user_id, program_id, current_streak, longest_streak, None, total_completed
    )


# ===== WEEKLY CHECKLISTS =====


async def get_weekly_checklist(user_id: str, program_id: int, year: int, week: int):
    """Get weekly checklist for a specific ISO week."""
    if supabase is None:
        return None

    res = (
        supabase.table("winter_arc_weekly_checklists")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .eq("year", year)
        .eq("week_number", week)
        .limit(1)
        .execute()
    )
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else None


async def get_weekly_checklists_range(
    user_id: str, program_id: int, start_date: date, end_date: date
):
    """Get weekly checklists for a date range."""
    if supabase is None:
        return []

    res = (
        supabase.table("winter_arc_weekly_checklists")
        .select("*")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .gte("week_start_date", start_date.isoformat())
        .lte("week_end_date", end_date.isoformat())
        .order("year", desc=False)
        .order("week_number", desc=False)
        .execute()
    )
    return res.data if hasattr(res, "data") else res


async def update_weekly_checklist(
    user_id: str, program_id: int, year: int, week: int, updates: dict[str, bool]
):
    """Update or create weekly checklist with completion data."""
    if supabase is None:
        return None

    # Check if checklist exists for this week
    existing = await get_weekly_checklist(user_id, program_id, year, week)

    # Valid weekly checklist fields
    valid_fields = {
        "strength_workouts_3_4",
        "cardio_sessions_2_3",
        "meal_prep",
        "progress_review",
        "plan_adjustment",
        "monk_mode_period",
        "reflection_on_principles",
        "planning_next_week",
    }

    # Filter to only valid fields
    data = {k: v for k, v in updates.items() if k in valid_fields}

    if existing:
        # Update existing checklist
        res = (
            supabase.table("winter_arc_weekly_checklists")
            .update(data)
            .eq("user_id", user_id)
            .eq("program_id", program_id)
            .eq("year", year)
            .eq("week_number", week)
            .execute()
        )
    else:
        # Create new checklist
        week_start, week_end = get_week_start_end(year, week)
        data["user_id"] = user_id
        data["program_id"] = program_id
        data["year"] = year
        data["week_number"] = week
        data["week_start_date"] = week_start.isoformat()
        data["week_end_date"] = week_end.isoformat()
        res = supabase.table("winter_arc_weekly_checklists").insert(data).execute()

    result_data = res.data if hasattr(res, "data") else res
    updated_checklist = result_data[0] if result_data else None

    # Update streaks if checklist was completed
    if updated_checklist and updated_checklist.get("is_fully_completed"):
        await update_weekly_streak(user_id, program_id)

    return updated_checklist


async def update_weekly_streak(user_id: str, program_id: int):
    """Recalculate and update weekly streak based on completed checklists."""
    if supabase is None:
        return

    # Get all completed weekly checklists ordered by year/week desc
    res = (
        supabase.table("winter_arc_weekly_checklists")
        .select("year,week_number,is_fully_completed")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .eq("is_fully_completed", True)
        .order("year", desc=True)
        .order("week_number", desc=True)
        .execute()
    )
    completed = res.data if hasattr(res, "data") else res

    if not completed:
        # No completed checklists - reset streaks
        await _update_progress_streaks(user_id, program_id, None, None, 0, 0)
        return

    # Calculate current streak (consecutive weeks from this week backwards)
    current_year, current_week = get_iso_week_info(datetime.now(UTC).date())
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    last_year, last_week = None, None

    for entry in completed:
        year = entry["year"]
        week = entry["week_number"]

        if last_year is None:
            # First entry - check if it's current week or last week
            if (year == current_year and week == current_week) or (
                year == current_year and week == current_week - 1
            ):
                current_streak = 1
                temp_streak = 1
                last_year, last_week = year, week
            else:
                # Streak broken
                temp_streak = 1
        else:
            # Check if consecutive week
            expected_week = last_week - 1
            expected_year = last_year

            if expected_week < 1:
                # Handle year boundary
                expected_year -= 1
                expected_week = 52  # Approximate

            if year == expected_year and week == expected_week:
                temp_streak += 1
                if last_year >= current_year and last_week >= current_week - 1:
                    current_streak = temp_streak
                last_year, last_week = year, week
            else:
                # Streak broken
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
                last_year, last_week = year, week

    longest_streak = max(longest_streak, temp_streak, current_streak)
    total_completed = len(completed)

    await _update_progress_streaks(
        user_id, program_id, None, None, current_streak, longest_streak, total_completed
    )


async def _update_progress_streaks(
    user_id: str,
    program_id: int,
    current_daily_streak: int | None = None,
    longest_daily_streak: int | None = None,
    current_weekly_streak: int | None = None,
    longest_weekly_streak: int | None = None,
    total_days_completed: int | None = None,
    total_weeks_completed: int | None = None,
):
    """Internal helper to update streak data in user_progress table."""
    if supabase is None:
        return

    data = {}
    if current_daily_streak is not None:
        data["current_daily_streak"] = current_daily_streak
    if longest_daily_streak is not None:
        data["longest_daily_streak"] = longest_daily_streak
    if current_weekly_streak is not None:
        data["current_weekly_streak"] = current_weekly_streak
    if longest_weekly_streak is not None:
        data["longest_weekly_streak"] = longest_weekly_streak
    if total_days_completed is not None:
        data["total_days_completed"] = total_days_completed
    if total_weeks_completed is not None:
        data["total_weeks_completed"] = total_weeks_completed

    # Check if progress record exists
    res_check = (
        supabase.table("winter_arc_user_progress")
        .select("id")
        .eq("user_id", user_id)
        .eq("program_id", program_id)
        .limit(1)
        .execute()
    )
    exists = bool((res_check.data if hasattr(res_check, "data") else res_check) or [])

    if exists:
        supabase.table("winter_arc_user_progress").update(data).eq(
            "user_id", user_id
        ).eq("program_id", program_id).execute()
    else:
        data["user_id"] = user_id
        data["program_id"] = program_id
        supabase.table("winter_arc_user_progress").insert(data).execute()


# ===== HELPER FOR CURRENT DATE =====


async def get_or_create_today_checklist(user_id: str, program_id: int):
    """Get or create today's daily checklist."""
    today = datetime.now(UTC).date()
    existing = await get_daily_checklist(user_id, program_id, today)
    if existing:
        return existing

    # Create empty checklist for today
    return await update_daily_checklist(user_id, program_id, today, {})


async def get_or_create_current_week_checklist(user_id: str, program_id: int):
    """Get or create current week's checklist."""
    year, week = get_iso_week_info(datetime.now(UTC).date())
    existing = await get_weekly_checklist(user_id, program_id, year, week)
    if existing:
        return existing

    # Create empty checklist for this week
    return await update_weekly_checklist(user_id, program_id, year, week, {})
