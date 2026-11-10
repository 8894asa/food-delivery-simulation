"""標準ライブラリの優先度キューによる離散イベントシミュレーション。"""
from dataclasses import dataclass
import heapq
import itertools
import math
from campus_delivery_sim.config import SimulationConfig
from campus_delivery_sim.models.courier import Courier
from campus_delivery_sim.models.location import TravelTimes
from campus_delivery_sim.models.order import Order
from campus_delivery_sim.models.store import Store
from campus_delivery_sim.simulation.arrivals import Arrival, generate_arrivals
from campus_delivery_sim.simulation.matching import match_orders


@dataclass
class SimulationResult:
    config: SimulationConfig
    orders: dict[str, Order]
    couriers: dict[str, Courier]


def run_simulation(config: SimulationConfig,
                   arrivals: list[Arrival] | None = None) -> SimulationResult:
    """観測終了時点で停止する。終了後の提供・配達は完了扱いにしない。"""
    stores = {s.id: Store(s) for s in config.stores}
    orders: dict[str, Order] = {}
    couriers: dict[str, Courier] = {}
    events: list[tuple] = []
    sequence = itertools.count()
    travel = TravelTimes(config.round_trip_minutes)

    def schedule(time: float, kind: str, payload: object) -> None:
        # 同時刻は提供・配達完了を先に処理し、到着は入力順に処理する。
        heapq.heappush(events, (time, 1 if kind == "arrival" else 0,
                               next(sequence), kind, payload))

    def start_next(store: Store, now: float) -> None:
        if store.current_order_id is None and store.queue:
            order = orders[store.queue.popleft()]
            store.current_order_id = order.id
            order.preparation_started_at = now
            schedule(now + 60 / store.config.orders_per_hour, "ready", order.id)

    for arrival in generate_arrivals(config) if arrivals is None else arrivals:
        if (not math.isfinite(arrival.time) or arrival.time < 0
                or arrival.time >= config.duration_minutes):
            raise ValueError("到着時刻は0以上、観測終了時刻未満にしてください")
        if arrival.store_id not in stores or arrival.kind not in ("delivery", "visitor"):
            raise ValueError("到着イベントの店舗IDまたは種別が不正です")
        schedule(arrival.time, "arrival", arrival)

    while events:
        now, _, _, kind, payload = heapq.heappop(events)
        if now > config.duration_minutes:
            break
        if kind == "arrival":
            arrival = payload
            store = stores[arrival.store_id]
            order_id = f"order-{len(orders) + 1}"
            is_delivery = arrival.kind == "delivery"
            order = Order(order_id, arrival.store_id,
                          "delivery" if is_delivery else "personal", now,
                          arrival.destination_id if is_delivery else None)
            orders[order_id] = order
            if not is_delivery:
                courier_id = f"visitor-{len(couriers) + 1}"
                couriers[courier_id] = Courier(courier_id, arrival.store_id, order_id,
                                               now, arrival.participates, arrival.destination_id)
                order.courier_id = courier_id
            store.queue.append(order_id)
            start_next(store, now)
        elif kind == "ready":
            order = orders[payload]
            store = stores[order.store_id]
            order.ready_at = now
            store.current_order_id = None
            if order.kind == "delivery":
                store.ready_deliveries.append(order.id)
            else:
                order.picked_up_at = now
                courier = couriers[order.courier_id]
                courier.departed_at = now
                courier.delivery_order_ids = match_orders(store, courier)
                for delivery_id in courier.delivery_order_ids:
                    delivery = orders[delivery_id]
                    delivery.courier_id = courier.id
                    delivery.picked_up_at = now
                    schedule(now + travel.outbound_minutes(store.config.location_id,
                                                           delivery.destination_id),
                             "delivered", delivery_id)
            start_next(store, now)
        elif kind == "delivered":
            orders[payload].delivered_at = now
    return SimulationResult(config, orders, couriers)
