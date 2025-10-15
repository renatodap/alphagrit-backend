from typing import Optional

from pydantic import BaseModel, Field


class ProfileUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    bio: Optional[str] = Field(default=None, max_length=2000)
    avatar_url: Optional[str] = None
    language: Optional[str] = None
    unit_preference: Optional[str] = None

