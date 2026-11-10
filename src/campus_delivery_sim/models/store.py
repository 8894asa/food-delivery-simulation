"""店舗ごとの共通FIFOキューと完成済み配達注文。"""
from collections import deque
from dataclasses import dataclass, field
from campus_delivery_sim.config import StoreConfig


@dataclass
class Store:
    config: StoreConfig
    queue: deque[str] = field(default_factory=deque)
    ready_deliveries: deque[str] = field(default_factory=deque)
    current_order_id: str | None = None
