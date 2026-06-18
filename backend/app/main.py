from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api import adapter_router, router
from app.core.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    start_scheduler()

    try:
        yield
    finally:
        shutdown_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Predictive Waste API",
        description=(
            "API untuk menerima data produksi harian, "
            "menyimpan request prediksi WIP ke database, "
            "menjalankan prediksi secara async, "
            "dan menyediakan status pemrosesan."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(router)
    app.include_router(adapter_router)
    return app


app = create_app()