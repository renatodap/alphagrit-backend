from supabase import create_client

from app.core.config import settings

if not settings.supabase_url or not settings.supabase_service_key:
    # Defer actual client creation until configured; consumers must handle None
    supabase = None  # type: ignore[assignment]
else:
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
