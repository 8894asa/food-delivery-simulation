"""出発時点で完成している注文を、完成順に割り当てる。"""
from campus_delivery_sim.models.courier import Courier
from campus_delivery_sim.models.store import Store


def match_orders(store: Store, courier: Courier) -> tuple[str, ...]:
    if not courier.participates:
        return ()
    return tuple(store.ready_deliveries.popleft()
                 for _ in range(min(courier.capacity, len(store.ready_deliveries))))
