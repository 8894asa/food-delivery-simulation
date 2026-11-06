"""JSON で読み込めるシミュレーション条件。時間の単位は分。"""
from dataclasses import dataclass, field
import json
import math
from pathlib import Path


def positive(name: str, value: float, *, zero: bool = False) -> None:
    if not math.isfinite(value) or (value < 0 if zero else value <= 0):
        raise ValueError(f"{name} は有限の{'0以上' if zero else '正'}の数にしてください")


@dataclass(frozen=True)
class StoreConfig:
    id: str = "store-1"
    location_id: str = "shop"
    orders_per_hour: float = 100
    delivery_orders_per_hour: float = 20
    visitors_per_hour: float = 60

    def __post_init__(self) -> None:
        if not self.id or not self.location_id:
            raise ValueError("店舗IDと地点IDは空にできません")
        positive("orders_per_hour", self.orders_per_hour)
        positive("delivery_orders_per_hour", self.delivery_orders_per_hour, zero=True)
        positive("visitors_per_hour", self.visitors_per_hour, zero=True)


@dataclass(frozen=True)
class SimulationConfig:
    duration_minutes: float = 120
    participation_rate: float = 0.5
    round_trip_minutes: float = 15
    seed: int = 42
    destination_ids: tuple[str, ...] = ("campus",)
    stores: tuple[StoreConfig, ...] = field(default_factory=lambda: (StoreConfig(),))

    def __post_init__(self) -> None:
        positive("duration_minutes", self.duration_minutes)
        positive("round_trip_minutes", self.round_trip_minutes, zero=True)
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("seed は整数にしてください")
        if not math.isfinite(self.participation_rate) or not 0 <= self.participation_rate <= 1:
            raise ValueError("participation_rate は0〜1にしてください")
        if not self.stores or len({s.id for s in self.stores}) != len(self.stores):
            raise ValueError("店舗は1件以上、店舗IDは重複なしにしてください")
        if (not self.destination_ids or isinstance(self.destination_ids, str)
                or any(not isinstance(x, str) or not x for x in self.destination_ids)):
            raise ValueError("配達先の地点IDを1件以上指定してください")

    @classmethod
    def from_json(cls, path: str | Path) -> "SimulationConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if "stores" in data:
            data["stores"] = tuple(StoreConfig(**s) for s in data["stores"])
        if "destination_ids" in data:
            if not isinstance(data["destination_ids"], list):
                raise ValueError("destination_ids は地点IDの配列にしてください")
            data["destination_ids"] = tuple(data["destination_ids"])
        return cls(**data)
