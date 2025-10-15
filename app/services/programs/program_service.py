from app.infra.supabase.client import supabase
from app.infra.payments import stripe_client  # noqa: F401
import stripe


async def list_programs():
    if supabase is None:
        return []
    res = supabase.table("programs").select("*").execute()
    return res.data if hasattr(res, "data") else res


async def get_program(program_id: int, user: dict):
    if supabase is None:
        return {"id": program_id, "member": False}
    res = supabase.table("programs").select("*").eq("id", program_id).limit(1).execute()
    data = res.data if hasattr(res, "data") else res
    program = data[0] if data else None
    if not program:
        return None
    membership = (
        supabase.table("user_programs")
        .select("id")
        .eq("user_id", user.get("sub"))
        .eq("program_id", program_id)
        .execute()
    )
    program["member"] = bool((membership.data if hasattr(membership, "data") else membership) or [])
    return program


async def create_program_checkout(program_id: int, user_id: str, tier: str = "standard"):
    price_id = None
    title = "Program"
    price_cents = 0
    if supabase is not None:
        pr = (
            supabase.table("programs")
            .select("title,stripe_price_id,stripe_price_standard_id,stripe_price_premium_id")
            .eq("id", program_id)
            .limit(1)
            .execute()
        )
        row = (pr.data if hasattr(pr, "data") else pr) or []
        if row:
            title = row[0].get("title") or title
            # prefer new tiered fields; fallback to legacy stripe_price_id
            if tier == "premium":
                price_id = row[0].get("stripe_price_premium_id") or row[0].get("stripe_price_id")
            else:
                price_id = row[0].get("stripe_price_standard_id") or row[0].get("stripe_price_id")
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
        success_url="https://wagnerfit.app/success",
        cancel_url="https://wagnerfit.app/cancel",
    )
    if supabase is not None:
        supabase.table("purchases").insert(
            {
                "user_id": user_id,
                "item_type": "program",
                "item_id": program_id,
                "price_cents": int(price_cents),
                "stripe_session_id": session.id,
                "tier": tier,
                "status": "pending",
            }
        ).execute()
    return {"checkout_url": session.url}
