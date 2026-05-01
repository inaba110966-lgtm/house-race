from pydantic import BaseModel
from typing import Any, Optional


class AnalysisRequest(BaseModel):
    query: str
    race_id: Optional[str] = None
    top_k: int = 10


class AnalysisResponse(BaseModel):
    query: str
    analysis: str
    sources: list[dict[str, Any]]
    race_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    collection: str = "races"  # "races" | "horses"
    top_k: int = 5
    filters: Optional[dict[str, Any]] = None


class SearchResponse(BaseModel):
    results: list[dict[str, Any]]
    query: str


class IndexRequest(BaseModel):
    data_path: str
    data_type: str  # "race" | "horse" | "result"
    overwrite: bool = False


class IndexResponse(BaseModel):
    indexed_count: int
    collection: str
    message: str
