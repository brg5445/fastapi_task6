from fastapi import FastAPI, Request

from src.core.config import settings
from src.core.logging import logger

from src.api import users, categories, locations, posts, comments, auth


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


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