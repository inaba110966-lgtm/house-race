"""
RAG (Retrieval-Augmented Generation) エンジン

1. クエリをベクトル化
2. Qdrant から関連レース/馬データを検索
3. コンテキストを構築
4. Claude にプロンプトを送信して分析を生成
"""

import anthropic
import logging
from typing import Any

from app.core.config import get_settings
from app.core.vector_store import vector_store
from app.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """あなたはJRA（日本中央競馬会）の競馬分析の専門家AIです。
JRA-VANの過去レースデータを参照して、正確で実用的な競馬分析を行います。

分析の際は以下の観点を考慮してください:
- 馬の過去成績・適性（コース・距離・馬場状態・季節）
- 騎手・調教師のパターンと相性
- 血統傾向（父系・母父の特性）
- 近走の内容（上がりタイム・位置取り・着差）
- 斤量・馬体重の変化
- オッズ・人気と実力の乖離

回答は根拠を明示し、数値データを活用した論理的な分析を心がけてください。
不確かな情報については明示的にその旨を伝えてください。"""


class RagEngine:
    def __init__(self):
        settings = get_settings()
        self._llm = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model
        self._settings = settings

    async def analyze(
        self,
        query: str,
        race_id: str | None = None,
        top_k: int = 10,
    ) -> dict[str, Any]:
        """
        RAGによる競馬分析を実行する

        Args:
            query: ユーザーの質問/分析リクエスト
            race_id: 特定レースのIDで絞り込む場合
            top_k: 検索する関連文書数

        Returns:
            analysis: 分析テキスト
            sources: 参照したデータの一覧
        """
        embedding_svc = get_embedding_service()

        # 1. クエリのベクトル化
        query_vector = await embedding_svc.embed_text_async(query)

        # 2. 関連データを検索
        race_filters = {"race_id": race_id} if race_id else None
        race_results, horse_results = await self._search_relevant_data(
            query_vector, top_k=top_k, race_filters=race_filters
        )

        # 3. コンテキスト構築
        context = self._build_context(race_results, horse_results)

        # 4. Claude で分析生成
        analysis = await self._generate_analysis(query, context)

        sources = [r["payload"] for r in race_results] + [r["payload"] for r in horse_results]

        return {
            "query": query,
            "analysis": analysis,
            "sources": sources[:top_k],
        }

    async def _search_relevant_data(
        self,
        query_vector: list[float],
        top_k: int,
        race_filters: dict | None = None,
    ) -> tuple[list[dict], list[dict]]:
        settings = self._settings
        race_results = await vector_store.search(
            collection=settings.race_collection,
            query_vector=query_vector,
            limit=top_k,
            filters=race_filters,
        )
        horse_results = await vector_store.search(
            collection=settings.horse_collection,
            query_vector=query_vector,
            limit=top_k // 2,
        )
        return race_results, horse_results

    def _build_context(
        self,
        race_results: list[dict],
        horse_results: list[dict],
    ) -> str:
        parts = []

        if race_results:
            parts.append("=== 関連レースデータ ===")
            for i, r in enumerate(race_results, 1):
                p = r["payload"]
                parts.append(
                    f"[レース{i}] スコア:{r['score']:.3f}\n{p.get('text', '')}"
                )

        if horse_results:
            parts.append("\n=== 関連馬データ ===")
            for i, r in enumerate(horse_results, 1):
                p = r["payload"]
                parts.append(
                    f"[馬{i}] スコア:{r['score']:.3f}\n{p.get('text', '')}"
                )

        return "\n\n".join(parts) if parts else "関連データが見つかりませんでした。"

    async def _generate_analysis(self, query: str, context: str) -> str:
        import asyncio

        user_message = f"""以下のJRA-VANデータを参考に、質問に答えてください。

【参照データ】
{context}

【質問・分析リクエスト】
{query}"""

        loop = asyncio.get_event_loop()

        def _call_claude():
            response = self._llm.messages.create(
                model=self._model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text

        return await loop.run_in_executor(None, _call_claude)

    async def search_similar(
        self,
        query: str,
        collection: str = "races",
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        """セマンティック検索のみ（分析なし）"""
        embedding_svc = get_embedding_service()
        query_vector = await embedding_svc.embed_text_async(query)

        settings = self._settings
        col_name = (
            settings.race_collection if collection == "races" else settings.horse_collection
        )
        return await vector_store.search(
            collection=col_name,
            query_vector=query_vector,
            limit=top_k,
            filters=filters,
        )


_engine: RagEngine | None = None


def get_rag_engine() -> RagEngine:
    global _engine
    if _engine is None:
        _engine = RagEngine()
    return _engine
