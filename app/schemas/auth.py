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


# Login
class LoginRequest(BaseModel):
    email:EmailStr
    password:str=Field(min_length=8,max_length=100)

class TokenResponse(BaseModel):
    access_token:str
    token_type:str