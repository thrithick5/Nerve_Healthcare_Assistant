# ./start.sh
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import Settings
from app.database.connection import init_db
from app.dependencies import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.requests")

settings = get_settings()

os.makedirs("data", exist_ok=True)

init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Healthcare Assistant with RAG capabilities"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.effective_cors_origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX if settings.CORS_ORIGIN_REGEX else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Response %s %s %s", request.method, request.url.path, response.status_code)
    return response

app.include_router(router, prefix="/api/v1")
