from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logging import logger

from src.api import users, categories, locations, posts, comments, auth

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

app.include_router(users.router)
app.include_router(categories.router)
app.include_router(locations.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(auth.router)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)