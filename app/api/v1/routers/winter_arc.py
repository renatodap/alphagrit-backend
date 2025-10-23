"""Winter Arc API Router - Endpoints for progress tracking, checklists, achievements, and leaderboard."""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps.auth import get_current_user, has_ebook_access, has_community_access, is_premium_tier
from app.services.winter_arc import (
    achievements_service,
    checklist_service,
    leaderboard_service,
    progress_service,
    suggestions_service,
)

router = APIRouter()


# ===== Access Control Endpoints =====


@router.get("/programs/{program_id}/check-access")
async def check_access(program_id: int, user=Depends(get_current_user)):
    """
    Check user's access levels for Winter Arc program.

    Returns:
    - has_ebook_access: bool
    - has_community_access: bool
    - is_premium: bool
    - product_type: str | None
    """
    user_id = user.get("sub") or user.get("id")

    ebook_access = await has_ebook_access(user_id, program_id)
    community_access = await has_community_access(user_id, program_id)
    premium = await is_premium_tier(user_id, program_id)

    # Determine product type
    product_type = None
    if premium:
        product_type = "community_premium"
    elif community_access:
        product_type = "community_standard"
    elif ebook_access:
        product_type = "ebook_only"

    return {
        "has_ebook_access": ebook_access,
        "has_community_access": community_access,
        "is_premium": premium,
        "product_type": product_type,
    }


# ===== DTOs =====


class UpdateProgressIn(BaseModel):
    mission_statement: str | None = None
    current_weight_kg: float | None = None
    height_cm: float | None = None
    age: int | None = None
    gender: str | None = None
    activity_level: str | None = None
    goal: str | None = None
    bmr: float | None = None
    tdee: float | None = None
    target_calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    show_on_leaderboard: bool | None = None


class CreateSnapshotIn(BaseModel):
    weight_kg: float
    notes: str | None = None


class UpdateDailyChecklistIn(BaseModel):
    wake_up_early: bool | None = None
    ten_min_silence: bool | None = None
    morning_hydration: bool | None = None
    workout: bool | None = None
    clean_eating: bool | None = None
    review_mission: bool | None = None
    small_sacrifice: bool | None = None
    moment_silence: bool | None = None
    act_of_honor: bool | None = None
    small_overcoming: bool | None = None


class UpdateWeeklyChecklistIn(BaseModel):
    strength_workouts_3_4: bool | None = None
    cardio_sessions_2_3: bool | None = None
    meal_prep: bool | None = None
    progress_review: bool | None = None
    plan_adjustment: bool | None = None
    monk_mode_period: bool | None = None
    reflection_on_principles: bool | None = None
    planning_next_week: bool | None = None


# ===== PROGRESS ENDPOINTS =====


@router.get("/programs/{program_id}/progress")
async def get_progress(program_id: int, user=Depends(get_current_user)):
    """Get user's Winter Arc progress for a program."""
    progress = await progress_service.get_user_progress(user["sub"], program_id)
    if not progress:
        # Return empty progress object instead of 404
        return {
            "user_id": user["sub"],
            "program_id": program_id,
            "current_daily_streak": 0,
            "longest_daily_streak": 0,
            "current_weekly_streak": 0,
            "longest_weekly_streak": 0,
        }
    return progress


@router.put("/programs/{program_id}/progress")
async def update_progress(
    program_id: int, payload: UpdateProgressIn, user=Depends(get_current_user)
):
    """Update user's Winter Arc progress."""
    return await progress_service.create_or_update_progress(
        user["sub"], program_id, **payload.model_dump(exclude_unset=True)
    )


@router.post("/programs/{program_id}/progress/timer")
async def increment_timer(
    program_id: int, minutes: int = 3, user=Depends(get_current_user)
):
    """Increment timer completion count."""
    return await progress_service.increment_timer_completions(
        user["sub"], program_id, minutes
    )


@router.post("/programs/{program_id}/progress/snapshots")
async def create_snapshot(
    program_id: int, payload: CreateSnapshotIn, user=Depends(get_current_user)
):
    """Create a progress snapshot."""
    return await progress_service.create_progress_snapshot(
        user["sub"], program_id, payload.weight_kg, payload.notes
    )


@router.get("/programs/{program_id}/progress/snapshots")
async def get_snapshots(program_id: int, limit: int = 50, user=Depends(get_current_user)):
    """Get progress snapshots."""
    return await progress_service.get_progress_snapshots(user["sub"], program_id, limit)


# ===== CHECKLIST ENDPOINTS =====


@router.get("/programs/{program_id}/checklists/daily/today")
async def get_today_checklist(program_id: int, user=Depends(get_current_user)):
    """Get or create today's daily checklist."""
    return await checklist_service.get_or_create_today_checklist(
        user["sub"], program_id
    )


@router.get("/programs/{program_id}/checklists/daily/{checklist_date}")
async def get_daily_checklist(
    program_id: int, checklist_date: date, user=Depends(get_current_user)
):
    """Get daily checklist for a specific date."""
    return await checklist_service.get_daily_checklist(
        user["sub"], program_id, checklist_date
    )


@router.put("/programs/{program_id}/checklists/daily/{checklist_date}")
async def update_daily_checklist(
    program_id: int,
    checklist_date: date,
    payload: UpdateDailyChecklistIn,
    user=Depends(get_current_user),
):
    """Update daily checklist for a specific date."""
    updates = payload.model_dump(exclude_unset=True)
    result = await checklist_service.update_daily_checklist(
        user["sub"], program_id, checklist_date, updates
    )

    # Trigger post suggestions and achievement checks
    await suggestions_service.check_and_trigger_suggestions(user["sub"], program_id)
    await achievements_service.check_and_unlock_achievements(user["sub"], program_id)
    await leaderboard_service.update_user_leaderboard_score(user["sub"], program_id)

    return result


@router.get("/programs/{program_id}/checklists/daily/range")
async def get_daily_checklists_range(
    program_id: int,
    start_date: date,
    end_date: date,
    user=Depends(get_current_user),
):
    """Get daily checklists for a date range."""
    return await checklist_service.get_daily_checklists_range(
        user["sub"], program_id, start_date, end_date
    )


@router.get("/programs/{program_id}/checklists/weekly/current")
async def get_current_week_checklist(program_id: int, user=Depends(get_current_user)):
    """Get or create current week's checklist."""
    return await checklist_service.get_or_create_current_week_checklist(
        user["sub"], program_id
    )


@router.get("/programs/{program_id}/checklists/weekly/{year}/{week}")
async def get_weekly_checklist(
    program_id: int, year: int, week: int, user=Depends(get_current_user)
):
    """Get weekly checklist for a specific ISO week."""
    return await checklist_service.get_weekly_checklist(
        user["sub"], program_id, year, week
    )


@router.put("/programs/{program_id}/checklists/weekly/{year}/{week}")
async def update_weekly_checklist(
    program_id: int,
    year: int,
    week: int,
    payload: UpdateWeeklyChecklistIn,
    user=Depends(get_current_user),
):
    """Update weekly checklist for a specific ISO week."""
    updates = payload.model_dump(exclude_unset=True)
    result = await checklist_service.update_weekly_checklist(
        user["sub"], program_id, year, week, updates
    )

    # Trigger post suggestions and achievement checks
    await suggestions_service.check_and_trigger_suggestions(user["sub"], program_id)
    await achievements_service.check_and_unlock_achievements(user["sub"], program_id)
    await leaderboard_service.update_user_leaderboard_score(user["sub"], program_id)

    return result


@router.get("/programs/{program_id}/checklists/weekly/range")
async def get_weekly_checklists_range(
    program_id: int,
    start_date: date,
    end_date: date,
    user=Depends(get_current_user),
):
    """Get weekly checklists for a date range."""
    return await checklist_service.get_weekly_checklists_range(
        user["sub"], program_id, start_date, end_date
    )


# ===== ACHIEVEMENTS ENDPOINTS =====


@router.get("/programs/{program_id}/achievements")
async def get_all_achievements():
    """Get all available achievements."""
    return await achievements_service.get_all_achievements()


@router.get("/programs/{program_id}/achievements/user")
async def get_user_achievements(program_id: int, user=Depends(get_current_user)):
    """Get user's unlocked achievements."""
    return await achievements_service.get_user_achievements(user["sub"], program_id)


@router.get("/programs/{program_id}/achievements/progress")
async def get_achievement_progress(program_id: int, user=Depends(get_current_user)):
    """Get user's progress toward all achievements."""
    return await achievements_service.get_achievement_progress(user["sub"], program_id)


@router.post("/programs/{program_id}/achievements/check")
async def check_achievements(program_id: int, user=Depends(get_current_user)):
    """Manually check and unlock achievements."""
    newly_unlocked = await achievements_service.check_and_unlock_achievements(
        user["sub"], program_id
    )
    await leaderboard_service.update_user_leaderboard_score(user["sub"], program_id)
    return {"newly_unlocked": newly_unlocked}


# ===== LEADERBOARD ENDPOINTS =====


@router.get("/programs/{program_id}/leaderboard")
async def get_leaderboard(program_id: int, limit: int = 100, offset: int = 0):
    """Get the leaderboard for a program."""
    return await leaderboard_service.get_leaderboard(program_id, limit, offset)


@router.get("/programs/{program_id}/leaderboard/me")
async def get_my_leaderboard_position(program_id: int, user=Depends(get_current_user)):
    """Get current user's leaderboard position."""
    return await leaderboard_service.get_user_leaderboard_position(
        user["sub"], program_id
    )


@router.get("/programs/{program_id}/leaderboard/context")
async def get_leaderboard_context(
    program_id: int, context_size: int = 5, user=Depends(get_current_user)
):
    """Get leaderboard entries around user's position."""
    return await leaderboard_service.get_leaderboard_context(
        user["sub"], program_id, context_size
    )


# ===== POST SUGGESTIONS ENDPOINTS =====


@router.get("/programs/{program_id}/suggestions")
async def get_suggestions(program_id: int, user=Depends(get_current_user)):
    """Get active post suggestions for user."""
    return await suggestions_service.get_active_suggestions(user["sub"], program_id)


@router.post("/programs/{program_id}/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion(
    program_id: int, suggestion_id: int, user=Depends(get_current_user)
):
    """Dismiss a post suggestion."""
    return await suggestions_service.dismiss_suggestion(suggestion_id)


@router.post("/programs/{program_id}/suggestions/{suggestion_id}/posted")
async def mark_suggestion_posted(
    program_id: int, suggestion_id: int, user=Depends(get_current_user)
):
    """Mark a suggestion as posted."""
    return await suggestions_service.mark_suggestion_posted(suggestion_id)


@router.post("/programs/{program_id}/suggestions/check")
async def check_suggestions(program_id: int, user=Depends(get_current_user)):
    """Manually check and trigger suggestions."""
    return await suggestions_service.check_and_trigger_suggestions(
        user["sub"], program_id
    )
