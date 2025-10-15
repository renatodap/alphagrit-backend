from datetime import date
from typing import Optional

from pydantic import BaseModel


class MetricCreateIn(BaseModel):
    date: date
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    photo_url: Optional[str] = None
    note: Optional[str] = None

