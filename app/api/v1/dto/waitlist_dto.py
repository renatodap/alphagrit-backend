from typing import Literal

from pydantic import BaseModel, EmailStr


class WaitlistIn(BaseModel):
    email: EmailStr
    language: Literal["en", "pt"] = "en"

