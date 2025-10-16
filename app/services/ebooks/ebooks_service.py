from app.infra.supabase.client import supabase
from app.infra.payments import stripe_client  # noqa: F401  # ensure stripe key set
import stripe


async def list_ebooks():
    if supabase is None:
        return []
    res = supabase.table("ebooks").select("*").execute()
    return res.data if hasattr(res, "data") else res


async def get_ebook_by_slug(slug: str, user: dict):
    if supabase is None:
        return {"slug": slug, "owned": False}
    res = supabase.table("ebooks").select("*").eq("slug", slug).limit(1).execute()
    data = res.data if hasattr(res, "data") else res
    ebook = data[0] if data else None
    if not ebook:
        return None
    # Check ownership (simplified)
    own = (
        supabase.table("purchases")
        .select("id")
        .eq("user_id", user.get("sub"))
        .eq("item_type", "ebook")
        .eq("item_id", ebook["id"])
        .eq("status", "paid")
        .execute()
    )
    owned = bool((own.data if hasattr(own, "data") else own) or [])
    ebook["owned"] = owned
    return ebook


async def create_checkout(ebook_id: int, user_id: str):
    from app.core.config import settings
    base_url = getattr(settings, 'frontend_url', 'https://wagnerfit.app')

    price_cents = 99900
    price_id = None
    title = "Ebook"
    if supabase is not None:
        er = supabase.table("ebooks").select("title,price_cents,stripe_price_id").eq("id", ebook_id).limit(1).execute()
        row = (er.data if hasattr(er, "data") else er) or []
        if row:
            title = row[0].get("title") or title
            price_cents = row[0].get("price_cents") or price_cents
            price_id = row[0].get("stripe_price_id")

    if price_id:
        line_items = [{"price": price_id, "quantity": 1}]
    else:
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(price_cents),
                    "product_data": {"name": title},
                },
                "quantity": 1,
            }
        ]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=f"{base_url}/success",
        cancel_url=f"{base_url}/cancel",
    )

    if supabase is not None:
        supabase.table("purchases").insert(
            {
                "user_id": user_id,
                "item_type": "ebook",
                "item_id": ebook_id,
                "price_cents": int(price_cents),
                "stripe_session_id": session.id,
                "status": "pending",
            }
        ).execute()
    return {"checkout_url": session.url}


async def create_combo_checkout(ebook_id: int, user_id: str, tier: str = "standard"):
    from app.core.config import settings
    base_url = getattr(settings, 'frontend_url', 'https://wagnerfit.app')

    combo_price_id = None
    title = "Ebook + Program"
    price_cents = None
    program_id = None
    if supabase is not None:
        er = (
            supabase.table("ebooks")
            .select("title,price_cents,program_id,program_combo_price_id,program_combo_premium_price_id")
            .eq("id", ebook_id)
            .limit(1)
            .execute()
        )
        row = (er.data if hasattr(er, "data") else er) or []
        if row:
            title = f"{row[0].get('title')} + Program"
            price_cents = row[0].get("price_cents")
            program_id = row[0].get("program_id")
            combo_price_id = row[0].get("program_combo_price_id")
    line_items = []
    if combo_price_id and tier == "standard":
        line_items = [{"price": combo_price_id, "quantity": 1}]
        total_cents = price_cents or 0
    elif tier == "premium":
        # try premium combo price id if present
        if supabase is not None:
            premium_price = row[0].get("program_combo_premium_price_id") if row else None  # type: ignore[name-defined]
        else:
            premium_price = None
        if premium_price:
            line_items = [{"price": premium_price, "quantity": 1}]
            total_cents = price_cents or 0
        else:
            total_cents = int((price_cents or 0) * 1.8)
            line_items = [
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": total_cents,
                        "product_data": {"name": f"{title} + Program (Premium)"},
                    },
                    "quantity": 1,
                }
            ]
    else:
        # fallback: single custom line for combo
        total_cents = int((price_cents or 0) * 1.5)  # naive combo price (adjust in DB)
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": total_cents,
                    "product_data": {"name": title},
                },
                "quantity": 1,
            }
        ]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=f"{base_url}/success",
        cancel_url=f"{base_url}/cancel",
    )

    if supabase is not None:
        supabase.table("purchases").insert(
            {
                "user_id": user_id,
                "item_type": "combo",
                "item_id": program_id,
                "price_cents": int(total_cents),
                "stripe_session_id": session.id,
                "tier": tier,
                "status": "pending",
            }
        ).execute()
    return {"checkout_url": session.url}
