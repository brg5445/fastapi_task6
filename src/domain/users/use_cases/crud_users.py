from sqlalchemy.orm import Session
from src.infrastructure.database.models.user_models import UserModel
from src.schemas.users import UserCreate, UserUpdate
from src.core.exceptions.domain_exceptions import (
    UserNicknameIsNotUniqueException,
    UserNotFoundByNicknameException,
    UserEmailIsNotUniqueException
)
from src.core.security import get_password_hash


class MethodsForUser:
    def get(self, db: Session, skip: int = 0, limit: int = 20):
        return db.query(UserModel).offset(skip).limit(limit).all()

    def get_detail(self, db: Session, nickname: str):
        user = db.query(UserModel).filter(UserModel.nickname == nickname).first()
        if not user:
            raise UserNotFoundByNicknameException(nickname=nickname)
        return user

    def create(self, db: Session, payload: UserCreate):
        if db.query(UserModel).filter(UserModel.nickname == payload.nickname).first():
            raise UserNicknameIsNotUniqueException(nickname=payload.nickname)

        if db.query(UserModel).filter(UserModel.email == payload.email).first():
            raise UserEmailIsNotUniqueException(email=payload.email)

        user = UserModel(
            nickname=payload.nickname,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            bio_info=payload.bio_info,
            hashed_password=get_password_hash(payload.password)
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, nickname: str, payload: UserUpdate):
        user = db.query(UserModel).filter(UserModel.nickname == nickname).first()
        if not user:
            raise UserNotFoundByNicknameException(nickname=nickname)

        if payload.email != user.email:
            if db.query(UserModel).filter(UserModel.email == payload.email).first():
                raise UserEmailIsNotUniqueException(email=payload.email)

        user.first_name = payload.first_name
        user.last_name = payload.last_name
        user.email = payload.email
        user.bio_info = payload.bio_info

        db.commit()
        db.refresh(user)
        return user

    def destroy(self, db: Session, nickname: str):
        user = db.query(UserModel).filter(UserModel.nickname == nickname).first()
        if not user:
            raise UserNotFoundByNicknameException(nickname=nickname)

        db.delete(user)
        db.commit()