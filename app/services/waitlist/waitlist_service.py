from app.infra.supabase.client import supabase


async def add_to_waitlist(email: str, language: str):
    email_lc = email.lower()
    # If Supabase isn't configured, return a stub for local dev
    if supabase is None:
        return {"id": None, "email": email_lc, "language": language}

    # Prevent duplicates explicitly (more predictable than relying on errors)
    existing = (
        supabase.table("waitlist").select("id").eq("email", email_lc).limit(1).execute()
    )
    data = existing.data if hasattr(existing, "data") else existing
    if data:
        return {"duplicate": True}

    inserted = (
        supabase.table("waitlist")
        .insert({"email": email_lc, "language": language})
        .select("id,email,language")
        .single()
        .execute()
    )
    return inserted.data if hasattr(inserted, "data") else inserted

