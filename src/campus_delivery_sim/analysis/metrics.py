"""配達時間は完了済み配達注文を対象に集計し、未配達数も併記する。"""
import math
from campus_delivery_sim.simulation.engine import SimulationResult


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def percentile(values: list[float], fraction: float) -> float | None:
    """昇順の順位を切り上げる nearest-rank 法。"""
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def summarize(result: SimulationResult) -> dict:
    deliveries = [o for o in result.orders.values() if o.kind == "delivery"]
    completed = [o for o in deliveries if o.delivered_at is not None]
    pending = [o for o in deliveries if o.delivered_at is None]
    durations = [o.delivered_at - o.ordered_at for o in completed]
    return {
        "duration_minutes": result.config.duration_minutes,
        "seed": result.config.seed,
        "delivery_orders": len(deliveries),
        "personal_orders": len(result.orders) - len(deliveries),
        "participating_visitors": sum(c.participates for c in result.couriers.values()),
        "completed_deliveries": len(completed),
        "undelivered_orders": len(pending),
        "undelivered_rate": len(pending) / len(deliveries) if deliveries else None,
        "pending_by_stage": {
            "queued": sum(o.preparation_started_at is None for o in pending),
            "preparing": sum(o.preparation_started_at is not None and o.ready_at is None for o in pending),
            "awaiting_courier": sum(o.ready_at is not None and o.picked_up_at is None for o in pending),
            "in_transit": sum(o.picked_up_at is not None for o in pending),
        },
        "completed_delivery_minutes": {
            "mean": mean(durations),
            "p90": percentile(durations, 0.9),
            "max": max(durations) if durations else None,
            "mean_queue_wait": mean([o.preparation_started_at - o.ordered_at for o in completed]),
            "mean_preparation": mean([o.ready_at - o.preparation_started_at for o in completed]),
            "mean_courier_wait": mean([o.picked_up_at - o.ready_at for o in completed]),
            "mean_outbound_travel": mean([o.delivered_at - o.picked_up_at for o in completed]),
        },
    }
