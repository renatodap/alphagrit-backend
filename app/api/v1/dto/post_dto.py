from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreatePostIn(BaseModel):
    message: Optional[str] = Field(default=None, max_length=4000)
    photo_url: Optional[str] = None
    visibility: Literal["public", "private"] = "public"

