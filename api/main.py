from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.cache import TTLCache
from api.limits import BodyLimitMiddleware, Limits
from api.middleware.logging_mw import RequestLoggingMiddleware
from api.middleware.request_id import RequestIdMiddleware
from api.routes import answer, chat, eligibility, evaluate, health, ingest, search
from core.config import get_settings
from core.exceptions import AppError
from core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Germany Masters Eligibility Assistant", version="0.1.0")

    cfg = get_settings().serve
    app.state.limits = Limits(cfg)  # counters live per app, so every test app starts at zero
    app.state.answer_cache = TTLCache(cfg.answer_cache_entries, cfg.answer_cache_ttl_s)

    # added last runs first: request_id must wrap the logging middleware, which wraps the body cap
    app.add_middleware(BodyLimitMiddleware, max_bytes=cfg.max_body_bytes)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().serve.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "request_id": getattr(request.state, "request_id", "-")},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        # FastAPI's default echoes the request body: a profile must never come back in an error
        errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"detail": errors, "request_id": getattr(request.state, "request_id", "-")},
        )

    modules = (health, search, answer, chat, ingest, evaluate, eligibility)
    for module in modules:
        app.include_router(module.router)
    # the access log names a path only if it is one of ours; anything else was chosen by the client
    app.state.known_paths = {route.path for module in modules for route in module.router.routes}
    return app


app = create_app()
