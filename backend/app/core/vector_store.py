from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
from typing import Any
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

VECTOR_SIZE = 1024  # voyage-3 embedding dimension


def _make_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_url:
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def _make_async_client() -> AsyncQdrantClient:
    settings = get_settings()
    if settings.qdrant_url:
        return AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    return AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


class VectorStore:
    def __init__(self):
        self._client: QdrantClient | None = None
        self._async_client: AsyncQdrantClient | None = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = _make_client()
        return self._client

    @property
    def async_client(self) -> AsyncQdrantClient:
        if self._async_client is None:
            self._async_client = _make_async_client()
        return self._async_client

    def ensure_collections(self) -> None:
        settings = get_settings()
        existing = {c.name for c in self.client.get_collections().collections}
        for name in [settings.race_collection, settings.horse_collection]:
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {name}")

    async def upsert(self, collection: str, points: list[PointStruct]) -> None:
        await self.async_client.upsert(collection_name=collection, points=points)

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict]:
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = await self.async_client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [
            {"score": r.score, "payload": r.payload, "id": str(r.id)}
            for r in results
        ]

    def close(self) -> None:
        if self._client:
            self._client.close()


vector_store = VectorStore()
