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

        # Get metadata from Stripe checkout session
        # Stripe metadata should include: product_type, tier
        metadata = data_object.get("metadata", {})

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

            # Determine product_type and tier from purchase metadata or Stripe metadata
            # Priority: Stripe metadata > Purchase data > Defaults
            product_type = (
                metadata.get("product_type")
                or purchase.get("product_type")
                or "community_standard"  # default
            )
            tier = metadata.get("tier") or purchase.get("tier")

            # Set tier based on product_type if not explicitly provided
            if tier is None:
                if product_type == "ebook_only":
                    tier = None  # No community tier for ebook-only
                elif product_type == "community_premium":
                    tier = "premium"
                else:
                    tier = "standard"

            # Grant access based on item_type
            item_type = purchase.get("item_type")
            item_id = purchase.get("item_id")
            user_id = purchase["user_id"]

            program_id = None

            # Determine program_id based on item_type
            if item_type == "ebook":
                # For ebook purchases, get program_id from ebooks table
                try:
                    ebook_res = (
                        supabase.table("ebooks")
                        .select("program_id")
                        .eq("id", item_id)
                        .limit(1)
                        .execute()
                    )
                    ebook_data = ebook_res.data if hasattr(ebook_res, "data") else ebook_res
                    if ebook_data:
                        program_id = ebook_data[0].get("program_id")
                except Exception:
                    pass

            elif item_type in ("program", "combo"):
                # For program/combo purchases, item_id is already the program_id
                program_id = item_id

            # Grant membership if we have a program_id
            if program_id and user_id:
                try:
                    enrollment_data = {
                        "user_id": user_id,
                        "program_id": program_id,
                        "product_type": product_type,
                    }

                    # Only add tier if it's not None (e.g., community purchases)
                    if tier is not None:
                        enrollment_data["tier"] = tier

                    supabase.table("user_programs").insert(enrollment_data).execute()
                except Exception:
                    pass

    elif event_type == "payment_intent.payment_failed" and supabase is not None:
        intent_id = data_object.get("id")
        supabase.table("purchases").update({"status": "failed"}).eq(
            "stripe_payment_intent", intent_id
        ).execute()
    return {"received": True}
