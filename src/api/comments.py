from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
import uuid

from fastapi import UploadFile, File
from fastapi.responses import FileResponse

from ..domain.comments.use_cases.crud_comments import MethodsForComment
from ..infrastructure.database.database import get_db
from ..schemas.comments import CommentCreate, CommentOut, CommentUpdate
from src.core.exceptions.domain_exceptions import (
    CommentNotFoundByIDException,
    CommentDontCreateException,
    PostNotFoundByIDException,
)
from src.core.security import get_current_user
from src.infrastructure.database.models.user_models import UserModel

router = APIRouter(prefix='/comments', tags=['Комментарии'])

UPLOAD_DIR = "uploads/comments"

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp"
}

MAX_FILE_SIZE = 5 * 1024 * 1024

@router.get('/', response_model=List[CommentOut], summary='Комментарии:')
def list_comments(
    post_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    DataBase: Session = Depends(get_db),
) -> List[CommentOut]:
    use_case = MethodsForComment()
    try:
        return use_case.get(DataBase, post_id, skip, limit)
    except PostNotFoundByIDException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.get('/{comment_id}', response_model=CommentOut, summary='Получить комментарий:')
def get_comment(comment_id: int, DataBase: Session = Depends(get_db)) -> CommentOut:
    use_case = MethodsForComment()
    try:
        return use_case.get_detail(DataBase, comment_id)
    except CommentNotFoundByIDException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.post('/', response_model=CommentOut, status_code=status.HTTP_201_CREATED, summary='Создать комментарий:')
def create_comment(
    payload: CommentCreate,
    DataBase: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> CommentOut:
    use_case = MethodsForComment()
    try:
        return use_case.create(DataBase, payload, author_id=current_user.id)
    except CommentDontCreateException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.put('/{comment_id}', response_model=CommentOut, summary='Изменить комментарий:')
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    DataBase: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> CommentOut:
    use_case = MethodsForComment()
    try:
        return use_case.update(DataBase, comment_id, payload, current_user=current_user)
    except CommentNotFoundByIDException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())


@router.delete('/{comment_id}', status_code=status.HTTP_204_NO_CONTENT, summary='Удалить комментарий:')
def delete_comment(
    comment_id: int,
    DataBase: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    use_case = MethodsForComment()
    try:
        use_case.destroy(DataBase, comment_id, current_user=current_user)
    except CommentNotFoundByIDException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.get_detail())

@router.post("/{comment_id}/image", summary="Загрузить фото к комментарию")
async def upload_comment_image(
    comment_id: int,
    file: UploadFile = File(...),
    DataBase: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):

    ext = file.filename.split(".")[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Недопустимый формат файла"
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Файл слишком большой"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = f"{uuid.uuid4()}.{ext}"

    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    use_case = MethodsForComment()

    try:
        comment = use_case.add_image(
            DataBase,
            comment_id,
            filepath,
            current_user
        )

        return {
            "comment_id": comment.id,
            "image": filepath
        }

    except CommentNotFoundByIDException as e:
        raise HTTPException(
            status_code=404,
            detail=e.get_detail()
        )


@router.get("/{comment_id}/image", summary="Получить фото комментария")
def get_comment_image(comment_id: int, DataBase: Session = Depends(get_db)):
    use_case = MethodsForComment()
    try:
        comment = use_case.get_detail(DataBase, comment_id)
    except CommentNotFoundByIDException as e:
        raise HTTPException(status_code=404, detail=e.get_detail())

    if not comment.image:
        raise HTTPException(status_code=404, detail="У комментария нет фото")

    filepath = comment.image
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(filepath)
