from fastapi import APIRouter, HTTPException
from app.models.schemas import SearchRequest, SearchResponse
from app.services.rag import get_rag_engine

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    セマンティック検索: クエリに意味的に近いレース/馬データを返す。
    """
    try:
        engine = get_rag_engine()
        results = await engine.search_similar(
            query=request.query,
            collection=request.collection,
            top_k=request.top_k,
            filters=request.filters,
        )
        return SearchResponse(results=results, query=request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
