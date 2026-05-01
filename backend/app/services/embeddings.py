"""
Embedding サービス

Anthropic の voyage-3 モデルでテキストをベクトル化する。
バッチ処理とキャッシュに対応。
"""

import anthropic
import asyncio
import logging
from functools import lru_cache

from app.core.config import get_settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 96  # voyage-3 の推奨バッチサイズ


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.embedding_model

    def embed_text(self, text: str) -> list[float]:
        """単一テキストをベクトル化"""
        response = self._client.beta.messages.batches  # Voyage経由
        # Anthropic SDK の voyage embedding
        result = self._client.embeddings.create(
            model=self._model,
            input=[text],
        )
        return result.embeddings[0].embedding

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """複数テキストをバッチでベクトル化"""
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i: i + BATCH_SIZE]
            result = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            all_embeddings.extend(e.embedding for e in result.embeddings)
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
