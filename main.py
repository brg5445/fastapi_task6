from fastapi import FastAPI, Request

from src.core.config import settings
from src.core.logging import logger

# Импорт моделей (пока оставим, но ниже объясню как лучше)
from src.infrastructure.sqlite.models import (
    category_models,
    comment_models,
    location_models,
    post_models,
    user_models,
)

from src.api import users, categories, locations, posts, comments, auth


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


# 🔥 ЛОГИРОВАНИЕ (обязательное требование)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# Роутеры
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(locations.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(auth.router)