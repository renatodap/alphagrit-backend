import stripe

from app.core.config import settings

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key
