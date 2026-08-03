from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.middleware.logging_mw import RequestLoggingMiddleware
from api.middleware.request_id import RequestIdMiddleware
from api.routes import answer, evaluate, health, ingest, search
from core.exceptions import AppError
from core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="EngineerDoc AI", version="0.1.0")

    # added last runs first: request_id must wrap the logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "request_id": getattr(request.state, "request_id", "-")},
        )

    for module in (health, search, answer, ingest, evaluate):
        app.include_router(module.router)
    return app


app = create_app()
