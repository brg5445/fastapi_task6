from pydantic import BaseModel, field_validator
from datetime import datetime as dati


class CommentCreate(BaseModel):
    text: str
    post_id: int
    image: str | None = None

    @field_validator("text", mode="after")
    @staticmethod
    def check_text(text: str):
        if len(text) == 0 or len(text) > 500:
            raise ValueError(
                'Текст должен быть от 1 до 500 символов.'
            )
        return text


class CommentUpdate(BaseModel):
    text: str | None = None
    image: str | None = None


class CommentOut(BaseModel):
    id: int
    text: str
    post_id: int
    author_id: int
    created_at: dati
    image: str | None = None

    class Config:
        from_attributes = True
