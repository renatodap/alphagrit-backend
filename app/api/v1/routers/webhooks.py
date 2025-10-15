import json
from fastapi import APIRouter, Request
from app.core.config import settings
from app.infra.supabase.client import supabase
import stripe

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    event = None
    if settings.stripe_webhook_secret and sig_header:
        try:
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=settings.stripe_webhook_secret
            )
        except Exception:
            return {"received": False}
    else:
        # Attempt to parse without verification in non-production environments
        try:
            event = json.loads(payload.decode("utf-8"))
        except Exception:
            return {"received": False}

    event_type = event.get("type") if isinstance(event, dict) else event.type
    data_object = event.get("data", {}).get("object") if isinstance(event, dict) else event.data.object

    if event_type == "checkout.session.completed" and supabase is not None:
        session_id = data_object.get("id")
        payment_intent = data_object.get("payment_intent")
        # Flip purchase to paid
        res = (
            supabase.table("purchases")
            .update({"status": "paid", "stripe_payment_intent": payment_intent})
            .eq("stripe_session_id", session_id)
            .execute()
        )
        rows = res.data if hasattr(res, "data") else res
        if rows:
            purchase = rows[0]
            if purchase.get("item_type") in ("program", "combo") and purchase.get("item_id"):
                # grant membership for program purchases
                try:
                    supabase.table("user_programs").insert(
                        {
                            "user_id": purchase["user_id"],
                            "program_id": purchase["item_id"],
                            "tier": purchase.get("tier") or "standard",
                        }
                    ).execute()
                except Exception:
                    pass
    elif event_type == "payment_intent.payment_failed" and supabase is not None:
        intent_id = data_object.get("id")
        supabase.table("purchases").update({"status": "failed"}).eq(
            "stripe_payment_intent", intent_id
        ).execute()
    return {"received": True}
