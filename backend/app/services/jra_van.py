"""
JRA-VAN データパーサー

JRA-VANのデータ仕様に基づき、固定長テキスト形式のファイルを解析する。
主なレコード種別:
  RA  - レース情報
  SE  - 馬毎レース情報 (成績)
  HN  - 馬名等基本情報
  JC  - 騎手マスタ
  CH  - 調教師マスタ
"""

import struct
from pathlib import Path
from datetime import date, datetime
from typing import Iterator
import logging
import json
import csv

from app.models.race import RaceInfo, HorseEntry, RaceResult
from app.models.horse import HorseProfile, HorseRaceRecord

logger = logging.getLogger(__name__)

VENUE_CODE_MAP = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
    "05": "東京", "06": "中山", "07": "中京", "08": "京都",
    "09": "阪神", "10": "小倉",
}

SURFACE_CODE_MAP = {"1": "芝", "2": "ダート", "3": "障害"}
DIRECTION_CODE_MAP = {"1": "左", "2": "右", "3": "直線", "4": "障害"}
GRADE_CODE_MAP = {
    "A": "G1", "B": "G2", "C": "G3",
    "D": "OP", "E": "L", "F": "3勝",
    "G": "2勝", "H": "1勝", "I": "新馬", "J": "未勝利",
}
TRACK_COND_MAP = {"1": "良", "2": "稍重", "3": "重", "4": "不良"}
SEX_CODE_MAP = {"1": "牡", "2": "牝", "3": "騸"}


def _parse_date(s: str) -> date | None:
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        try:
            return datetime.strptime(s, "%Y%m%d").date()
        except ValueError:
            pass
    return None


def _parse_int(s: str) -> int:
    s = s.strip()
    return int(s) if s.isdigit() else 0


def _parse_float(s: str) -> float:
    s = s.strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


class JraVanParser:
    """JRA-VAN固定長形式ファイルのパーサー"""

    def parse_race_file(self, file_path: Path) -> Iterator[RaceInfo]:
        """RA (レース情報) ファイルをパース"""
        with open(file_path, encoding="cp932", errors="replace") as f:
            for line in f:
                line = line.rstrip("\r\n")
                if len(line) < 100:
                    continue
                try:
                    yield self._parse_ra_record(line)
                except Exception as e:
                    logger.debug(f"RAレコードパースエラー: {e} | {line[:50]}")

    def _parse_ra_record(self, line: str) -> RaceInfo:
        """RAレコード1行をRaceInfoに変換 (JRA-VAN RA仕様に準拠)"""
        def _f(start: int, length: int) -> str:
            return line[start: start + length].strip()

        race_date_str = _f(8, 8)
        venue_code = _f(16, 2)
        race_num = _parse_int(_f(22, 2))
        race_name = _f(24, 60)
        grade_code = _f(84, 1)
        surface_code = _f(85, 1)
        direction_code = _f(86, 1)
        distance = _parse_int(_f(87, 4))
        track_cond_code = _f(91, 1)
        weather_code = _f(92, 1)
        prize_1st = _parse_int(_f(93, 8))

        race_id = f"{race_date_str}{venue_code}{race_num:02d}"
        return RaceInfo(
            race_id=race_id,
            race_date=_parse_date(race_date_str) or date.today(),
            venue_code=venue_code,
            venue_name=VENUE_CODE_MAP.get(venue_code, venue_code),
            race_number=race_num,
            race_name=race_name,
            grade=GRADE_CODE_MAP.get(grade_code, grade_code),
            surface=SURFACE_CODE_MAP.get(surface_code, ""),
            direction=DIRECTION_CODE_MAP.get(direction_code, ""),
            distance=distance,
            track_condition=TRACK_COND_MAP.get(track_cond_code, ""),
            prize_money=prize_1st,
        )

    def parse_result_file(self, file_path: Path) -> Iterator[HorseRaceRecord]:
        """SE (馬毎レース情報) ファイルをパース"""
        with open(file_path, encoding="cp932", errors="replace") as f:
            for line in f:
                line = line.rstrip("\r\n")
                if len(line) < 200:
                    continue
                try:
                    yield self._parse_se_record(line)
                except Exception as e:
                    logger.debug(f"SEレコードパースエラー: {e}")

    def _parse_se_record(self, line: str) -> HorseRaceRecord:
        def _f(start: int, length: int) -> str:
            return line[start: start + length].strip()

        race_date_str = _f(8, 8)
        venue_code = _f(16, 2)
        race_num = _parse_int(_f(22, 2))
        horse_num = _parse_int(_f(24, 2))
        horse_id = _f(26, 10)
        horse_name = _f(36, 36)
        sex_code = _f(72, 1)
        age = _parse_int(_f(73, 2))
        weight_carried = _parse_float(_f(75, 3))
        jockey_id = _f(78, 5)
        jockey_name = _f(83, 34)
        finishing_order_str = _f(117, 2)
        finish_time = _f(119, 8)
        margin = _f(127, 8)
        odds = _parse_float(_f(135, 7))
        popularity = _parse_int(_f(142, 2))
        horse_weight = _parse_int(_f(144, 3))
        horse_weight_diff_str = _f(147, 3)
        last_3f_str = _f(150, 4)
        corner_pos = _f(154, 16)
        trainer_id = _f(170, 5)
        trainer_name = _f(175, 34)

        race_id = f"{race_date_str}{venue_code}{race_num:02d}"
        finishing_order = _parse_int(finishing_order_str) or None
        last_3f = _parse_float(last_3f_str) / 10 if last_3f_str.isdigit() else None
        horse_weight_diff = (
            int(horse_weight_diff_str) if horse_weight_diff_str.lstrip("-").isdigit() else None
        )

        return HorseRaceRecord(
            horse_id=horse_id,
            horse_name=horse_name,
            race_id=race_id,
            race_date=_parse_date(race_date_str) or date.today(),
            venue_name=VENUE_CODE_MAP.get(venue_code, venue_code),
            race_name="",
            surface="",
            distance=0,
            track_condition="",
            finishing_order=finishing_order,
            horse_number=horse_num,
            weight_carried=weight_carried,
            jockey_name=jockey_name,
            finish_time=finish_time,
            margin=margin,
            last_3f=last_3f,
            horse_weight=horse_weight,
            horse_weight_diff=horse_weight_diff,
            odds=odds if odds > 0 else None,
            popularity=popularity or None,
            corner_positions=corner_pos,
        )

    def parse_horse_file(self, file_path: Path) -> Iterator[HorseProfile]:
        """HN (馬名等基本情報) ファイルをパース"""
        with open(file_path, encoding="cp932", errors="replace") as f:
            for line in f:
                line = line.rstrip("\r\n")
                if len(line) < 100:
                    continue
                try:
                    yield self._parse_hn_record(line)
                except Exception as e:
                    logger.debug(f"HNレコードパースエラー: {e}")

    def _parse_hn_record(self, line: str) -> HorseProfile:
        def _f(start: int, length: int) -> str:
            return line[start: start + length].strip()

        horse_id = _f(8, 10)
        horse_name = _f(18, 36)
        birth_date_str = _f(54, 8)
        sex_code = _f(62, 1)
        coat_color = _f(63, 4)
        sire = _f(67, 36)
        dam = _f(103, 36)
        dam_sire = _f(139, 36)
        trainer_id = _f(175, 5)
        trainer_name = _f(180, 34)
        owner_name = _f(214, 72)
        breeder_name = _f(286, 72)
        birth_place = _f(358, 8)

        return HorseProfile(
            horse_id=horse_id,
            horse_name=horse_name,
            birth_date=_parse_date(birth_date_str),
            sex=SEX_CODE_MAP.get(sex_code, sex_code),
            coat_color=coat_color,
            sire=sire,
            dam=dam,
            dam_sire=dam_sire,
            trainer_id=trainer_id,
            trainer_name=trainer_name,
            owner_name=owner_name,
            breeder_name=breeder_name,
            birth_place=birth_place,
        )

    def parse_csv_race(self, file_path: Path) -> Iterator[RaceInfo]:
        """CSV形式のレースデータをパース (JRA公開データ等)"""
        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    yield self._csv_row_to_race(row)
                except Exception as e:
                    logger.debug(f"CSV race parse error: {e}")

    def _csv_row_to_race(self, row: dict) -> RaceInfo:
        race_date = _parse_date(row.get("race_date", "").replace("-", ""))
        entries = []
        return RaceInfo(
            race_id=row.get("race_id", ""),
            race_date=race_date or date.today(),
            venue_code=row.get("venue_code", ""),
            venue_name=row.get("venue_name", ""),
            race_number=_parse_int(row.get("race_number", "0")),
            race_name=row.get("race_name", ""),
            grade=row.get("grade", ""),
            surface=row.get("surface", ""),
            direction=row.get("direction", ""),
            distance=_parse_int(row.get("distance", "0")),
            track_condition=row.get("track_condition", ""),
            weather=row.get("weather", ""),
            prize_money=_parse_int(row.get("prize_money", "0")),
            entries=entries,
        )

    def parse_json_data(self, file_path: Path) -> list[dict]:
        """JSON形式データの読み込み"""
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)


jra_van_parser = JraVanParser()
