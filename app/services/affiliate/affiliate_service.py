from urllib.parse import urlparse, parse_qs

from fastapi import HTTPException

from app.infra.supabase.client import supabase


def _validate_affiliate_url(url: str) -> None:
    parsed = urlparse(url)
    if "amazon." not in parsed.netloc.lower():
        raise HTTPException(status_code=400, detail="Invalid Amazon URL")
    qs = parse_qs(parsed.query)
    tag = qs.get("tag", [None])[0]
    if not tag:
        raise HTTPException(status_code=400, detail="Affiliate tag missing")


async def list_products():
    if supabase is None:
        return []
    res = supabase.table("affiliate_products").select("*").order("id").execute()
    return res.data if hasattr(res, "data") else res


async def create_product(payload: dict):
    _validate_affiliate_url(payload.get("amazon_url", ""))
    if supabase is None:
        return payload
    res = supabase.table("affiliate_products").insert(payload).execute()
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else payload


async def update_product(product_id: int, payload: dict):
    if "amazon_url" in payload:
        _validate_affiliate_url(payload["amazon_url"])
    if supabase is None:
        return {"id": product_id, **payload}
    res = supabase.table("affiliate_products").update(payload).eq("id", product_id).execute()
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else {"id": product_id, **payload}


async def delete_product(product_id: int):
    if supabase is None:
        return {"id": product_id, "deleted": True}
    res = supabase.table("affiliate_products").delete().eq("id", product_id).execute()
    data = res.data if hasattr(res, "data") else res
    return data[0] if data else {"id": product_id, "deleted": True}
