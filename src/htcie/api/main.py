"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import htcie
from htcie.api import dependencies
from htcie.api.routers import evaluate as evaluate_router
from htcie.api.routers import methods as methods_router
from htcie.core.loader import build_registry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context: load the correlation registry at startup."""
    dependencies.registry = build_registry()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="htcie — Heat Transfer Correlation Intelligence Engine",
        version=htcie.__version__,
        lifespan=lifespan,
    )
    # IMPORTANT: Do NOT add allow_credentials=True here. Browsers reject CORS
    # responses when allow_origins=["*"] and allow_credentials=True are both set
    # (security constraint: wildcard origin cannot allow credentials).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(evaluate_router.router)
    app.include_router(methods_router.router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "project": "htcie", "version": htcie.__version__}

    return app


app = create_app()
