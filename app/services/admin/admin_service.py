from app.infra.supabase.client import supabase


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
