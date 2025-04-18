from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

from src.entity.models import Role


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    avatar: str
    role: Role

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RequestEmail(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    token: str = Field(..., description="Token from email")
    new_password: str = Field(..., min_length=6, max_length=100)