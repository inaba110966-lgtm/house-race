"""
Embedding サービス

Voyage AI (voyage-3) でテキストをベクトル化する。
voyageai ライブラリを使用。
"""

import voyageai
import asyncio
import logging
from functools import lru_cache

from app.core.config import get_settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 128  # voyage-3 の最大バッチサイズ


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self._client = voyageai.Client(api_key=settings.voyage_api_key)
        self._model = settings.embedding_model

    def embed_text(self, text: str) -> list[float]:
        """単一テキストをベクトル化"""
        result = self._client.embed([text], model=self._model)
        return result.embeddings[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """複数テキストをバッチでベクトル化"""
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i: i + BATCH_SIZE]
            result = self._client.embed(batch, model=self._model)
            all_embeddings.extend(result.embeddings)
        return all_embeddings

    async def embed_text_async(self, text: str) -> list[float]:
        """非同期でテキストをベクトル化"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_text, text)

    async def embed_texts_async(self, texts: list[str]) -> list[list[float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_texts, texts)


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
