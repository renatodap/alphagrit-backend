from datetime import datetime

from pydantic import BaseModel


class Ebook(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    price_cents: int
    program_id: int | None
    created_at: datetime
