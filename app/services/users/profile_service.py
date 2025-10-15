from app.infra.supabase.client import supabase


async def get_profile(user):
    if supabase is None:
        return {"user_id": user.get("sub"), "profile": None}
    res = supabase.table("user_profiles").select("*").eq("user_id", user["sub"]).execute()
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else {}


async def update_profile(user, payload):
    if supabase is None:
        return {"user_id": user.get("sub"), **payload}
    res = (
        supabase.table("user_profiles").update(payload).eq("user_id", user["sub"]).execute()
    )
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else {}
