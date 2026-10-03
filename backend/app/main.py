# ./start.sh
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

import logging
import os

os.environ["ANONYMOUS_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = ""

try:
    import chromadb.telemetry.product.posthog as _chroma_posthog
    _chroma_posthog.Posthog.capture = lambda self, event: None
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import router
from app.core.config import Settings
from app.database.connection import init_db
from app.dependencies import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api.requests")

settings = get_settings()

os.makedirs("data", exist_ok=True)

if not init_db():
    logger.warning(
        "Starting without a verified database schema. Endpoints that need the "
        "database will recover automatically once it becomes reachable."
    )

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


@app.exception_handler(SQLAlchemyError)
async def database_unavailable(request: Request, exc: SQLAlchemyError):
    """Turn a database outage into a readable 503.

    Without this, the error reaches Starlette's ServerErrorMiddleware, which
    sits *outside* CORSMiddleware and answers with a bare text/plain 500 that
    carries no access-control-allow-origin header. The browser discards it,
    axios sees a request with no response, and the UI reports
    "Network error. Please check your connection." -- hiding a server fault
    behind a message that suggests the user is offline.

    Handlers registered here run in ExceptionMiddleware, which is inside
    CORSMiddleware, so this response does reach the browser.
    """
    logger.error(
        "database unavailable handling %s %s: %s",
        request.method, request.url.path, exc,
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Database temporarily unavailable. Please try again in a moment."},
    )
