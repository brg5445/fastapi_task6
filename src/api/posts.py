from typing import List
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..domain.posts.use_cases.crud_posts import MethodsForPost
from src.core.exceptions.domain_exceptions import (
    PostNotFoundByIDException,
    PostDontCreateException,
    PostDontChangeException,
)
from ..infrastructure.database.database import get_db
from ..schemas.posts import PostCreate, PostDetail, PostOut, PostUpdate
from src.core.security import get_current_user
from src.infrastructure.database.models.user_models import UserModel

router = APIRouter(prefix='/posts', tags=['Посты'])

UPLOAD_DIR = "uploads/posts"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.get('/', response_model=List[PostOut], summary='Публикации:')
def list_posts(
        skip: int = 0,
        limit: int = 20,
        published_only: bool = False,
        DataBase: Session = Depends(get_db)
) -> List[PostOut]:
    use_case = MethodsForPost()
    return use_case.get(DataBase, skip, limit, published_only)


@router.get('/{post_id}', response_model=PostDetail, summary='Получить публикацию:')
def get_post(post_id: int, DataBase: Session = Depends(get_db)) -> PostDetail:
    use_case = MethodsForPost()
    try:
        return use_case.get_detail(DataBase, post_id)
    except PostNotFoundByIDException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.post('/', response_model=PostOut, status_code=status.HTTP_201_CREATED, summary='Создать публикацию:')
def create_post(
        payload: PostCreate,
        DataBase: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
) -> PostOut:
    use_case = MethodsForPost()
    try:
        return use_case.create(DataBase, payload, author_id=current_user.id)
    except PostDontCreateException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.put('/{post_id}', response_model=PostOut, summary='Изменить публикацию:')
def update_post(
        post_id: int,
        payload: PostUpdate,
        DataBase: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
) -> PostOut:
    use_case = MethodsForPost()
    try:
        return use_case.update(DataBase, post_id, payload, current_user=current_user)
    except PostNotFoundByIDException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())
    except PostDontChangeException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.delete('/{post_id}', status_code=status.HTTP_204_NO_CONTENT, summary='Удалить публикацию:')
def delete_post(
        post_id: int,
        DataBase: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    use_case = MethodsForPost()
    try:
        use_case.destroy(DataBase, post_id, current_user=current_user)
    except PostNotFoundByIDException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.post("/{post_id}/image", summary="Загрузить фото к посту")
async def upload_post_image(
        post_id: int,
        file: UploadFile = File(...),
        DataBase: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):

    use_case = MethodsForPost()

    ext = file.filename.split(".")[-1].lower() if file.filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый формат. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимум {MAX_FILE_SIZE // 1024 // 1024} MB"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    try:

        post = use_case.add_image(
            DataBase,
            post_id,
            filepath,
            current_user
        )

        return {
            "post_id": post.id,
            "image": filepath
        }

    except PostNotFoundByIDException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.get_detail()
        )

    except PostDontChangeException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{post_id}/image", summary="Получить фото поста")
def get_post_image(post_id: int, DataBase: Session = Depends(get_db)):
    use_case = MethodsForPost()
    try:
        post = use_case.get_detail(DataBase, post_id)
    except PostNotFoundByIDException as e:
        raise HTTPException(status_code=404, detail=e.get_detail())

    if not post.image:
        raise HTTPException(status_code=404, detail="У поста нет фото")

    if not os.path.exists(post.image):
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(post.image)
