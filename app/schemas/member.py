from pydantic import BaseModel, Field


class MemberCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(default="member", min_length=2, max_length=50)


class MemberResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str