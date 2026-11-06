"""来店注文・配達注文と、実際に発生したイベント時刻。"""
from dataclasses import dataclass
from typing import Literal


@dataclass
class Order:
    id: str
    store_id: str
    kind: Literal["delivery", "personal"]
    ordered_at: float
    destination_id: str | None = None
    courier_id: str | None = None
    preparation_started_at: float | None = None
    ready_at: float | None = None
    picked_up_at: float | None = None
    delivered_at: float | None = None
