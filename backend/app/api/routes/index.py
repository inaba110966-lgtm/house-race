from fastapi import APIRouter, HTTPException, BackgroundTasks
from pathlib import Path
from app.models.schemas import IndexRequest, IndexResponse
from app.core.config import get_settings

router = APIRouter(prefix="/index", tags=["indexing"])


async def _run_indexing(data_path: str, data_type: str, overwrite: bool) -> int:
    from app.data_pipeline.indexer import DataIndexer
    indexer = DataIndexer()
    return await indexer.index(Path(data_path), data_type, overwrite=overwrite)


@router.post("", response_model=IndexResponse)
async def index_data(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    JRA-VANデータをQdrantにインデックスする。
    バックグラウンドで実行される。
    """
    path = Path(request.data_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Path not found: {request.data_path}")

    settings = get_settings()
    col = (
        settings.race_collection
        if request.data_type in ("race", "result")
        else settings.horse_collection
    )

    background_tasks.add_task(
        _run_indexing, request.data_path, request.data_type, request.overwrite
    )

    return IndexResponse(
        indexed_count=0,
        collection=col,
        message=f"インデックス処理をバックグラウンドで開始しました: {request.data_path}",
    )


@router.get("/status")
async def index_status():
    """Qdrantコレクションの状態を確認"""
    from app.core.vector_store import vector_store
    settings = get_settings()
    try:
        collections = {}
        for name in [settings.race_collection, settings.horse_collection]:
            info = vector_store.client.get_collection(name)
            collections[name] = {
                "points_count": info.points_count,
                "status": str(info.status),
            }
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
