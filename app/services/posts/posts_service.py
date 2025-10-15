from app.infra.supabase.client import supabase


async def list_posts(program_id: int, user: dict):
    if supabase is None:
        return []
    # Show public posts and private posts authored by user or admin
    # Visibility: 'public' or 'private'
    q = (
        supabase.table("posts")
        .select("*")
        .eq("program_id", program_id)
        .order("created_at", desc=True)
    )
    res = q.execute()
    posts = res.data if hasattr(res, "data") else res
    uid = user.get("sub")
    is_admin = "admin" in user.get("roles", [])
    visible = []
    for p in posts or []:
        if p.get("visibility") == "public":
            visible.append(p)
        elif p.get("visibility") == "private":
            if p.get("user_id") == uid or is_admin:
                visible.append(p)
    return visible


async def create_post(program_id: int, payload: dict, user: dict):
    if supabase is None:
        return {**payload, "program_id": program_id, "user_id": user.get("sub")}
    payload = {
        "program_id": program_id,
        "user_id": user.get("sub"),
        "message": payload.get("message"),
        "photo_url": payload.get("photo_url"),
        "visibility": payload.get("visibility", "public"),
    }
    # Server-side tier check: if private, require premium membership
    if payload["visibility"] == "private":
        mem = (
            supabase.table("user_programs")
            .select("tier")
            .eq("user_id", user.get("sub"))
            .eq("program_id", program_id)
            .limit(1)
            .execute()
        )
        row = (mem.data if hasattr(mem, "data") else mem) or []
        if not row or row[0].get("tier") != "premium":
            # mirror RLS; service-level guard for clearer error
            return {"error": {"code": "FORBIDDEN", "message": "Premium required for private posts"}}
    res = supabase.table("posts").insert(payload).execute()
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else payload
