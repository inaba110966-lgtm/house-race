from fastapi import APIRouter, HTTPException, Query
from app.core.vector_store import vector_store
from app.core.config import get_settings

router = APIRouter(prefix="/horses", tags=["horses"])


@router.get("/search")
async def search_horses(
    name: str = Query(..., description="馬名（部分一致）"),
    limit: int = Query(10, ge=1, le=50),
):
    """馬名でセマンティック検索"""
    try:
        settings = get_settings()
        from app.services.embeddings import get_embedding_service
        embedding_svc = get_embedding_service()
        query_vec = await embedding_svc.embed_text_async(f"馬名: {name}")

        results = await vector_store.search(
            collection=settings.horse_collection,
            query_vector=query_vec,
            limit=limit,
        )
        return {"horses": [r["payload"] for r in results], "query": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{horse_id}/history")
async def get_horse_history(horse_id: str):
    """馬の過去成績を取得"""
    try:
        settings = get_settings()
        from app.services.embeddings import get_embedding_service
        embedding_svc = get_embedding_service()
        query_vec = await embedding_svc.embed_text_async(horse_id)

        results = await vector_store.search(
            collection=settings.horse_collection,
            query_vector=query_vec,
            limit=50,
            filters={"horse_id": horse_id},
        )
        if not results:
            raise HTTPException(status_code=404, detail=f"Horse {horse_id} not found")
        return {
            "horse_id": horse_id,
            "records": [r["payload"] for r in results],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
