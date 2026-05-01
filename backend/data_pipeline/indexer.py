"""
JRA-VANデータ → Qdrant インデクサー

使い方:
  python -m data_pipeline.indexer --data-path ./data/jra_van --data-type race
  python -m data_pipeline.indexer --data-path ./data/jra_van --data-type horse
"""

import asyncio
import logging
from pathlib import Path
from typing import Literal

from qdrant_client.models import PointStruct

from app.core.config import get_settings
from app.core.vector_store import vector_store
from app.services.jra_van import jra_van_parser
from data_pipeline.vectorizer import vectorize_race, vectorize_horse_record

logger = logging.getLogger(__name__)

DataType = Literal["race", "horse", "result"]
UPSERT_BATCH = 64


class DataIndexer:
    def __init__(self):
        self._settings = get_settings()

    async def index(self, data_path: Path, data_type: DataType, overwrite: bool = False) -> int:
        vector_store.ensure_collections()

        if data_path.is_file():
            files = [data_path]
        else:
            ext_map = {"race": ["*.ra", "*.RA", "*.csv"], "horse": ["*.hn", "*.HN"], "result": ["*.se", "*.SE"]}
            patterns = ext_map.get(data_type, ["*"])
            files = [f for pat in patterns for f in data_path.glob(pat)]

        logger.info(f"Indexing {len(files)} files as {data_type}")

        total = 0
        for file_path in files:
            count = await self._index_file(file_path, data_type)
            total += count
            logger.info(f"  {file_path.name}: {count} points indexed")

        logger.info(f"Total indexed: {total}")
        return total

    async def _index_file(self, file_path: Path, data_type: DataType) -> int:
        points: list[PointStruct] = []
        collection = self._settings.race_collection

        if data_type == "race":
            for race in jra_van_parser.parse_race_file(file_path):
                points.append(await vectorize_race(race))

        elif data_type == "result":
            for record in jra_van_parser.parse_result_file(file_path):
                points.append(await vectorize_horse_record(record))
            collection = self._settings.horse_collection

        elif data_type == "horse":
            for profile in jra_van_parser.parse_horse_file(file_path):
                from data_pipeline.vectorizer import _make_id
                from app.services.embeddings import get_embedding_service
                text = profile.to_text()
                vec = await get_embedding_service().embed_text_async(text)
                from qdrant_client.models import PointStruct
                points.append(
                    PointStruct(
                        id=_make_id(f"profile_{profile.horse_id}"),
                        vector=vec,
                        payload={
                            "horse_id": profile.horse_id,
                            "horse_name": profile.horse_name,
                            "sire": profile.sire,
                            "dam": profile.dam,
                            "dam_sire": profile.dam_sire,
                            "trainer_name": profile.trainer_name,
                            "text": text,
                            "data_type": "horse_profile",
                        },
                    )
                )
            collection = self._settings.horse_collection

        # バッチでupsert
        for i in range(0, len(points), UPSERT_BATCH):
            batch = points[i: i + UPSERT_BATCH]
            await vector_store.upsert(collection, batch)

        return len(points)


async def _main():
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="JRA-VAN data indexer")
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--data-type", choices=["race", "horse", "result"], required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    indexer = DataIndexer()
    total = await indexer.index(Path(args.data_path), args.data_type, args.overwrite)
    print(f"Indexed {total} points")


if __name__ == "__main__":
    asyncio.run(_main())
