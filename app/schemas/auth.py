from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# Register
class RegisterRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    bio: str | None = None
    theme: str = "light"


class ProfileUpdate(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100
    )
    phone: str | None = Field(
        default=None,
        max_length=20
    )
    bio: str | None = Field(
        default=None,
        max_length=500
    )
    theme: Literal["light", "dark"] = "light"


# Login
class LoginRequest(BaseModel):
    email:EmailStr
    password:str=Field(min_length=8,max_length=100)

class TokenResponse(BaseModel):
    access_token:str
    token_type:str