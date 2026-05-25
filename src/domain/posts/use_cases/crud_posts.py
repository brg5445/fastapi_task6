from sqlalchemy.orm import Session
from src.infrastructure.database.models.post_models import PostModel
from src.infrastructure.database.models.user_models import UserModel
from src.infrastructure.database.models.category_models import CategoryModel
from src.infrastructure.database.models.location_models import LocationModel
from src.schemas.posts import PostCreate, PostUpdate
from src.core.exceptions.domain_exceptions import (
    PostNotFoundByIDException,
    PostDontCreateException,
    PostDontChangeException
)


class MethodsForPost:

    def get(
            self,
            db: Session,
            skip: int = 0,
            limit: int = 20,
            published_only: bool = False
    ):
        query = db.query(PostModel)
        if published_only:
            query = query.filter(PostModel.is_published == True)
        return query.offset(skip).limit(limit).all()

    def get_detail(self, db: Session, post_id: int):
        post = db.query(PostModel).filter(PostModel.id == post_id).first()
        if not post:
            raise PostNotFoundByIDException(id=post_id)
        return post

    def create(
            self,
            db: Session,
            payload: PostCreate,
            author_id: int
    ):
        category = (
            db.query(CategoryModel)
            .filter(CategoryModel.id == payload.category_id)
            .first()
        )
        location = (
            db.query(LocationModel)
            .filter(LocationModel.id == payload.location_id)
            .first()
        )
        if not category or not location:
            raise PostDontCreateException(
                "Категория или локация не найдены"
            )
        post = PostModel(
            title=payload.title,
            text=payload.text,
            pub_date=payload.pub_date,
            is_published=payload.is_published,
            image=payload.image,
            category_id=payload.category_id,
            location_id=payload.location_id,
            author_id=author_id,
        )
        try:
            db.add(post)
            db.commit()
            db.refresh(post)
            return post
        except Exception as e:
            db.rollback()
            raise PostDontCreateException(str(e))

    def update(
            self,
            db: Session,
            post_id: int,
            payload: PostUpdate,
            current_user: UserModel
    ):
        post = (
            db.query(PostModel)
            .filter(PostModel.id == post_id)
            .first()
        )
        if not post:
            raise PostNotFoundByIDException(id=post_id)
        if post.author_id != current_user.id:
            raise PostDontChangeException(
                "Вы не являетесь автором этого поста"
            )
        if payload.title is not None:
            post.title = payload.title
        if payload.text is not None:
            post.text = payload.text
        if payload.pub_date is not None:
            post.pub_date = payload.pub_date
        if payload.is_published is not None:
            post.is_published = payload.is_published
        if payload.image is not None:
            post.image = payload.image
        if payload.category_id is not None:
            category = (
                db.query(CategoryModel)
                .filter(CategoryModel.id == payload.category_id)
                .first()
            )
            if not category:
                raise PostDontChangeException(
                    "Категория не найдена"
                )
            post.category_id = payload.category_id
        if payload.location_id is not None:
            location = (
                db.query(LocationModel)
                .filter(LocationModel.id == payload.location_id)
                .first()
            )
            if not location:
                raise PostDontChangeException(
                    "Локация не найдена"
                )
            post.location_id = payload.location_id
        try:
            db.commit()
            db.refresh(post)
            return post
        except Exception as e:
            db.rollback()
            raise PostDontChangeException(str(e))

    def destroy(
            self,
            db: Session,
            post_id: int,
            current_user: UserModel
    ):
        post = (
            db.query(PostModel)
            .filter(PostModel.id == post_id)
            .first()
        )
        if not post:
            raise PostNotFoundByIDException(id=post_id)
        if post.author_id != current_user.id:
            raise PostDontChangeException(
                "Вы не являетесь автором этого поста"
            )
        try:
            db.delete(post)
            db.commit()
        except Exception as e:
            db.rollback()
            raise PostDontChangeException(str(e))

    def add_image(
            self,
            db: Session,
            post_id: int,
            image_path: str,
            current_user: UserModel
    ):
        post = (
            db.query(PostModel)
            .filter(PostModel.id == post_id)
            .first()
        )
        if not post:
            raise PostNotFoundByIDException(id=post_id)
        if post.author_id != current_user.id:
            raise PostDontChangeException(
                "Вы не являетесь автором этого поста"
            )
        if post.image:
            import os
            if os.path.exists(post.image):
                os.remove(post.image)
        post.image = image_path
        try:
            db.commit()
            db.refresh(post)
            return post
        except Exception as e:
            db.rollback()
            raise PostDontChangeException(str(e))
