from fastapi import APIRouter, HTTPException
from app.models.schemas import AnalysisRequest, AnalysisResponse
from app.services.rag import get_rag_engine

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisResponse)
async def analyze_race(request: AnalysisRequest):
    """
    RAGを使った競馬分析を実行する。
    JRA-VANの過去データを検索し、Claudeが分析・予測を生成する。
    """
    try:
        engine = get_rag_engine()
        result = await engine.analyze(
            query=request.query,
            race_id=request.race_id,
            top_k=request.top_k,
        )
        return AnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
