"""一定率の独立ポアソン過程による配達注文・来店者の発生。"""
from dataclasses import dataclass
import random
from typing import Literal
from campus_delivery_sim.config import SimulationConfig


@dataclass(frozen=True)
class Arrival:
    time: float
    store_id: str
    kind: Literal["delivery", "visitor"]
    destination_id: str = "campus"
    participates: bool = False


def generate_arrivals(config: SimulationConfig) -> list[Arrival]:
    rng = random.Random(config.seed)
    arrivals = []
    for store in config.stores:
        for kind, rate in (("delivery", store.delivery_orders_per_hour),
                           ("visitor", store.visitors_per_hour)):
            if rate == 0:
                continue
            time = rng.expovariate(rate / 60)
            while time < config.duration_minutes:
                destination = rng.choice(config.destination_ids)
                participates = kind == "visitor" and rng.random() < config.participation_rate
                arrivals.append(Arrival(time, store.id, kind, destination, participates))
                time += rng.expovariate(rate / 60)
    return sorted(arrivals, key=lambda a: a.time)
