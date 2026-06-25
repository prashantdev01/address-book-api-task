from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.logging_config import configure_logging
from app.middleware.idempotency import IdempotencyMiddleware
from app.routers import address_router
from app.schemas.response import APIResponse

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("application_startup", app=settings.app_name, version=settings.app_version)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("application_shutdown", app=settings.app_name)
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A RESTful address book API. "
        "Supports full CRUD on addresses and geospatial distance-based search."
    ),
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("request_validation_error", path=str(request.url), errors=exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=APIResponse.error("Invalid request data.").model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warning(
        "http_exception",
        path=str(request.url),
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse.error(exc.detail).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        path=str(request.url),
        method=request.method,
        exc_type=type(exc).__name__,
        exc=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse.error("An unexpected error occurred. Please try again later.").model_dump(),
    )


app.add_middleware(IdempotencyMiddleware)
app.include_router(address_router)


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check() -> APIResponse[dict]:
    return APIResponse.success(
        data={"version": settings.app_version},
        message="Service is healthy.",
    )
