"""User schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update schema."""

    display_name: str | None = None
    password: str | None = None


class User(UserBase):
    """User response schema."""

    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token payload data."""

    user_id: int
    username: str
