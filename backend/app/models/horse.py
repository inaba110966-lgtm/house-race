from pydantic import BaseModel
from typing import Optional
from datetime import date


class HorseProfile(BaseModel):
    """馬プロフィール"""
    horse_id: str
    horse_name: str
    birth_date: Optional[date] = None
    sex: str = ""
    coat_color: str = ""
    sire: str = ""        # 父
    dam: str = ""         # 母
    dam_sire: str = ""    # 母父
    trainer_name: str = ""
    trainer_id: str = ""
    owner_name: str = ""
    breeder_name: str = ""
    birth_place: str = ""

    def to_text(self) -> str:
        parts = [
            f"馬名: {self.horse_name}",
            f"性別: {self.sex}",
            f"毛色: {self.coat_color}",
            f"父: {self.sire}",
            f"母: {self.dam}",
            f"母父: {self.dam_sire}",
            f"調教師: {self.trainer_name}",
            f"馬主: {self.owner_name}",
            f"生産者: {self.breeder_name}",
            f"産地: {self.birth_place}",
        ]
        return "\n".join(p for p in parts if p.split(": ")[1])


class HorseRaceRecord(BaseModel):
    """馬の個別レース成績"""
    horse_id: str
    horse_name: str
    race_id: str
    race_date: date
    venue_name: str
    race_name: str
    grade: str = ""
    surface: str = ""
    distance: int = 0
    track_condition: str = ""
    finishing_order: Optional[int] = None
    horse_number: int = 0
    weight_carried: float = 0.0
    jockey_name: str = ""
    finish_time: str = ""
    margin: str = ""          # 着差
    last_3f: Optional[float] = None  # 上がり3F
    horse_weight: Optional[int] = None
    horse_weight_diff: Optional[int] = None
    odds: Optional[float] = None
    popularity: Optional[int] = None
    corner_positions: str = ""  # コーナー通過順

    def to_text(self) -> str:
        order_str = f"{self.finishing_order}着" if self.finishing_order else "除/取/中"
        return (
            f"{self.race_date} {self.venue_name} {self.race_name}"
            f"({self.grade}) {self.surface}{self.distance}m {self.track_condition} "
            f"→ {order_str} 騎手:{self.jockey_name} 斤量:{self.weight_carried} "
            f"タイム:{self.finish_time} 上がり:{self.last_3f or '-'}"
            f"({self.popularity}番人気/{self.odds}倍)"
        )


class HorseHistory(BaseModel):
    """馬の全成績履歴"""
    profile: HorseProfile
    records: list[HorseRaceRecord]

    def to_text(self) -> str:
        lines = [self.profile.to_text(), "", "【過去成績】"]
        for r in sorted(self.records, key=lambda x: x.race_date, reverse=True)[:20]:
            lines.append(r.to_text())
        return "\n".join(lines)

    @property
    def wins(self) -> int:
        return sum(1 for r in self.records if r.finishing_order == 1)

    @property
    def top3(self) -> int:
        return sum(1 for r in self.records if r.finishing_order and r.finishing_order <= 3)

    @property
    def total_races(self) -> int:
        return len(self.records)
