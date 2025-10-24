from app.infra.supabase.client import supabase


async def get_profile(user):
    if supabase is None:
        return {"user_id": user.get("sub"), "profile": None}

    user_id = user["sub"]

    # Get user profile
    res = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
    data = res.data if hasattr(res, "data") else res
    profile = data[0] if data else {}

    # Get Winter Arc tier from user_programs
    # Query the tier for the Winter Arc program
    tier_res = (
        supabase.table("user_programs")
        .select("tier, programs!inner(slug)")
        .eq("user_id", user_id)
        .eq("programs.slug", "winter-arc")
        .limit(1)
        .execute()
    )

    tier_data = tier_res.data if hasattr(tier_res, "data") else tier_res

    # Add winter_arc_tier to profile response
    if tier_data and len(tier_data) > 0:
        profile["winter_arc_tier"] = tier_data[0].get("tier")
    else:
        profile["winter_arc_tier"] = None

    return profile


async def update_profile(user, payload):
    if supabase is None:
        return {"user_id": user.get("sub"), **payload}
    res = (
        supabase.table("user_profiles").update(payload).eq("user_id", user["sub"]).execute()
    )
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else {}
