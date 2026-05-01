"""
テキスト → Embeddingベクトル変換

JRA-VANのレース/馬データをテキスト化してQdrantに格納するためのポイントを生成する。
"""

import uuid
from qdrant_client.models import PointStruct
from app.models.race import RaceInfo, RaceResult
from app.models.horse import HorseProfile, HorseRaceRecord, HorseHistory
from app.services.embeddings import get_embedding_service


def _make_id(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))


async def vectorize_race(race: RaceInfo) -> PointStruct:
    """RaceInfo → Qdrant PointStruct"""
    text = race.to_text()
    embedding_svc = get_embedding_service()
    vector = await embedding_svc.embed_text_async(text)
    return PointStruct(
        id=_make_id(race.race_id),
        vector=vector,
        payload={
            "race_id": race.race_id,
            "race_date": str(race.race_date),
            "venue_name": race.venue_name,
            "race_name": race.race_name,
            "grade": race.grade,
            "surface": race.surface,
            "distance": race.distance,
            "track_condition": race.track_condition,
            "text": text,
            "data_type": "race_info",
        },
    )


async def vectorize_result(result: RaceResult) -> PointStruct:
    """RaceResult → Qdrant PointStruct"""
    text = result.to_text()
    embedding_svc = get_embedding_service()
    vector = await embedding_svc.embed_text_async(text)
    return PointStruct(
        id=_make_id(f"result_{result.race_id}"),
        vector=vector,
        payload={
            "race_id": result.race_id,
            "race_date": str(result.race_date),
            "venue_name": result.venue_name,
            "race_name": result.race_name,
            "grade": result.grade,
            "surface": result.surface,
            "distance": result.distance,
            "track_condition": result.track_condition,
            "finishing_order": result.finishing_order,
            "text": text,
            "data_type": "race_result",
        },
    )


async def vectorize_horse_record(record: HorseRaceRecord) -> PointStruct:
    """HorseRaceRecord → Qdrant PointStruct (馬コレクション)"""
    text = record.to_text()
    embedding_svc = get_embedding_service()
    vector = await embedding_svc.embed_text_async(text)
    return PointStruct(
        id=_make_id(f"{record.horse_id}_{record.race_id}"),
        vector=vector,
        payload={
            "horse_id": record.horse_id,
            "horse_name": record.horse_name,
            "race_id": record.race_id,
            "race_date": str(record.race_date),
            "venue_name": record.venue_name,
            "race_name": record.race_name,
            "surface": record.surface,
            "distance": record.distance,
            "finishing_order": record.finishing_order,
            "jockey_name": record.jockey_name,
            "finish_time": record.finish_time,
            "last_3f": record.last_3f,
            "text": text,
            "data_type": "horse_record",
        },
    )


async def vectorize_horse_history(history: HorseHistory) -> list[PointStruct]:
    """HorseHistory (馬全成績) → 複数 PointStruct"""
    points = []
    # プロフィールもベクトル化
    profile_text = history.profile.to_text()
    embedding_svc = get_embedding_service()
    profile_vec = await embedding_svc.embed_text_async(profile_text)
    points.append(
        PointStruct(
            id=_make_id(f"profile_{history.profile.horse_id}"),
            vector=profile_vec,
            payload={
                "horse_id": history.profile.horse_id,
                "horse_name": history.profile.horse_name,
                "sire": history.profile.sire,
                "dam": history.profile.dam,
                "dam_sire": history.profile.dam_sire,
                "trainer_name": history.profile.trainer_name,
                "text": profile_text,
                "data_type": "horse_profile",
            },
        )
    )
    # 各成績をベクトル化
    for record in history.records:
        points.append(await vectorize_horse_record(record))
    return points
