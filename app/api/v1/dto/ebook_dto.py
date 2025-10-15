from pydantic import BaseModel


class EbookOut(BaseModel):
    id: int
    title: str
    description: str
    price_cents: int
    has_program: bool
