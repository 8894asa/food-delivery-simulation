"""地点IDによる参照と移動時間。経路別モデルへの差し替え箇所。"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    id: str


@dataclass(frozen=True)
class TravelTimes:
    round_trip_minutes: float

    def outbound_minutes(self, origin_id: str, destination_id: str) -> float:
        # 初期モデルでは、すべての地点間を往復時間の半分とする。
        return self.round_trip_minutes / 2
