from pydantic import BaseModel, Field
from typing import Literal

class MemberCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: Literal["admin", "member"] = "member"


class MemberResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str

class InviteAccept(BaseModel):
    token: str = Field(min_length=20)