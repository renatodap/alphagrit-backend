from app.infra.supabase.client import supabase


async def list_metrics(user: dict):
    if supabase is None:
        return []
    res = (
        supabase.table("user_metrics")
        .select("*")
        .eq("user_id", user.get("sub"))
        .order("date", desc=True)
        .execute()
    )
    return res.data if hasattr(res, "data") else res


async def create_metric(user: dict, payload: dict):
    if supabase is None:
        return {**payload, "user_id": user.get("sub")}
    rec = {**payload, "user_id": user.get("sub")}
    res = supabase.table("user_metrics").insert(rec).execute()
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else rec


async def delete_metric(user: dict, metric_id: int):
    if supabase is None:
        return {"id": metric_id, "deleted": True}
    res = (
        supabase.table("user_metrics")
        .delete()
        .eq("id", metric_id)
        .eq("user_id", user.get("sub"))
        .execute()
    )
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else {"id": metric_id, "deleted": True}
