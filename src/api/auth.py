from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import JWTError, jwt

from src.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token
)

from src.core.config import settings

from src.infrastructure.database.database import get_db
from src.infrastructure.database.models.user_models import UserModel

from src.schemas.token import Token

router = APIRouter(tags=["auth"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(UserModel).filter(
        UserModel.nickname == form_data.username
    ).first()

    if not user or not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный никнейм или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.nickname}
    )

    refresh_token = create_refresh_token(
        data={"sub": user.nickname}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_access_token(
    payload: RefreshTokenRequest
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:

        decoded = jwt.decode(
            payload.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        token_type = decoded.get("type")

        if token_type != "refresh":
            raise credentials_exception

        nickname = decoded.get("sub")

        if nickname is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    new_access_token = create_access_token(
        data={"sub": nickname}
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
