import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware


configure_logging()

logger = logging.getLogger("modelops.application")


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-Process-Time-MS",
        ],
    )

    application.add_middleware(RequestContextMiddleware)

    application.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    register_exception_handlers(application)

    return application


def register_exception_handlers(
    application: FastAPI,
) -> None:
    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "Request validation failed",
            extra={
                "path": request.url.path,
                "errors": error.errors(),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": "Request validation failed.",
                "errors": error.errors(),
            },
        )

    @application.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        error: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled application error",
            extra={
                "path": request.url.path,
                "error_type": type(error).__name__,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": ("An unexpected server error occurred.")},
        )


app = create_application()


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to ModelOps Doctor",
        "documentation": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }
