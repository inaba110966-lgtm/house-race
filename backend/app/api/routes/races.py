from fastapi import APIRouter, HTTPException, Query
from app.core.vector_store import vector_store
from app.core.config import get_settings

router = APIRouter(prefix="/races", tags=["races"])


@router.get("")
async def list_races(
    venue: str | None = Query(None, description="競馬場名 (例: 東京)"),
    grade: str | None = Query(None, description="グレード (例: G1)"),
    limit: int = Query(20, ge=1, le=100),
):
    """最近のレース一覧をVectorDBから取得する"""
    try:
        settings = get_settings()
        filters = {}
        if venue:
            filters["venue_name"] = venue
        if grade:
            filters["grade"] = grade

        # ダミークエリでフィルタ検索（全件取得の代替）
        from app.services.embeddings import get_embedding_service
        embedding_svc = get_embedding_service()
        query_vec = await embedding_svc.embed_text_async("レース情報")

        results = await vector_store.search(
            collection=settings.race_collection,
            query_vector=query_vec,
            limit=limit,
            filters=filters if filters else None,
        )
        return {"races": [r["payload"] for r in results], "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{race_id}")
async def get_race(race_id: str):
    """特定レースの詳細情報を取得する"""
    try:
        settings = get_settings()
        from app.services.embeddings import get_embedding_service
        embedding_svc = get_embedding_service()
        query_vec = await embedding_svc.embed_text_async(race_id)

        results = await vector_store.search(
            collection=settings.race_collection,
            query_vector=query_vec,
            limit=1,
            filters={"race_id": race_id},
        )
        if not results:
            raise HTTPException(status_code=404, detail=f"Race {race_id} not found")
        return results[0]["payload"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
