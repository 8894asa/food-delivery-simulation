"""一度だけ来店し、自分の商品を受け取って出発する人。"""
from dataclasses import dataclass


@dataclass
class Courier:
    id: str
    store_id: str
    personal_order_id: str
    arrived_at: float
    participates: bool
    destination_id: str
    capacity: int = 1
    departed_at: float | None = None
    delivery_order_ids: tuple[str, ...] = ()
