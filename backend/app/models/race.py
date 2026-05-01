from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class HorseEntry(BaseModel):
    """出走馬情報"""
    horse_number: int
    horse_name: str
    horse_id: str = ""
    age: int = 0
    sex: str = ""            # 牡/牝/騸
    weight_carried: float = 0.0  # 斤量
    jockey_name: str = ""
    jockey_id: str = ""
    trainer_name: str = ""
    trainer_id: str = ""
    odds: Optional[float] = None
    popularity: Optional[int] = None  # 人気順
    horse_weight: Optional[int] = None
    horse_weight_diff: Optional[int] = None


class RaceInfo(BaseModel):
    """レース基本情報"""
    race_id: str
    race_date: date
    venue_code: str
    venue_name: str
    race_number: int
    race_name: str
    grade: str = ""          # G1/G2/G3/OP/etc
    surface: str = ""        # 芝/ダート
    distance: int = 0        # メートル
    direction: str = ""      # 右/左/直線
    weather: str = ""
    track_condition: str = ""  # 良/稍重/重/不良
    prize_money: int = 0     # 1着賞金（万円）
    entries: list[HorseEntry] = Field(default_factory=list)

    def to_text(self) -> str:
        """RAG用テキスト表現"""
        lines = [
            f"レース名: {self.race_name}",
            f"開催日: {self.race_date}",
            f"競馬場: {self.venue_name}",
            f"グレード: {self.grade}" if self.grade else "",
            f"コース: {self.surface} {self.distance}m {self.direction}",
            f"馬場状態: {self.track_condition}",
            f"天候: {self.weather}",
            f"1着賞金: {self.prize_money}万円" if self.prize_money else "",
        ]
        if self.entries:
            lines.append(f"出走頭数: {len(self.entries)}頭")
            for e in self.entries[:5]:
                odds_str = f" (オッズ{e.odds}倍/{e.popularity}番人気)" if e.odds else ""
                lines.append(
                    f"  {e.horse_number}番 {e.horse_name} "
                    f"({e.age}歳{e.sex} 斤量{e.weight_carried}) "
                    f"騎手:{e.jockey_name} 調教師:{e.trainer_name}{odds_str}"
                )
        return "\n".join(l for l in lines if l)


class RaceResult(BaseModel):
    """レース結果"""
    race_id: str
    race_date: date
    venue_name: str
    race_name: str
    grade: str = ""
    surface: str = ""
    distance: int = 0
    track_condition: str = ""
    finishing_order: list[dict] = Field(default_factory=list)

    def to_text(self) -> str:
        lines = [
            f"【{self.race_name}】結果",
            f"開催: {self.race_date} {self.venue_name}",
            f"コース: {self.surface} {self.distance}m",
            f"馬場: {self.track_condition}",
            "着順:",
        ]
        for r in self.finishing_order[:10]:
            time_str = f" {r.get('finish_time', '')}" if r.get("finish_time") else ""
            lines.append(
                f"  {r.get('order', '')}着: {r.get('horse_name', '')} "
                f"騎手:{r.get('jockey_name', '')}{time_str}"
            )
        return "\n".join(lines)
