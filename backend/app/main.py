from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import get_settings
from app.core.vector_store import vector_store
from app.api.routes import analysis, search, races, horses, index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.app_name}")
    try:
        vector_store.ensure_collections()
        logger.info("Qdrant collections ready")
    except Exception as e:
        logger.warning(f"Qdrant not available at startup: {e}")
    yield
    vector_store.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="JRA-VANデータ × Vector DB × RAGによる競馬分析AIシステム",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(races.router, prefix="/api/v1")
    app.include_router(horses.router, prefix="/api/v1")
    app.include_router(index.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": settings.app_name}

    # フロントエンドの静的ファイル配信
    static_dir = Path("/app/frontend/dist")
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            return FileResponse(str(static_dir / "index.html"))

    return app


app = create_app()
