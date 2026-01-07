"""Authentication API endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from supervisor.database import get_db
from supervisor.models.user import User
from supervisor.schemas.user import Token, User as UserSchema
from supervisor.utils.security import verify_password, create_access_token
from supervisor.api.deps import get_current_active_user

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get current user information."""
    return current_user
