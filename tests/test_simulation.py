"""手計算できる時系列を使ったモデルの契約確認。"""
import unittest

from campus_delivery_sim.analysis.metrics import summarize
from campus_delivery_sim.config import SimulationConfig, StoreConfig
from campus_delivery_sim.simulation.arrivals import Arrival, generate_arrivals
from campus_delivery_sim.simulation.engine import run_simulation


def delivery(time, store="store-1"):
    return Arrival(time, store, "delivery", "building-a")


def visitor(time, participates=True, store="store-1"):
    return Arrival(time, store, "visitor", "building-b", participates)


class SimulationTests(unittest.TestCase):
    def test_shared_serial_queue_and_delivery_time_breakdown(self):
        result = run_simulation(SimulationConfig(), [delivery(0), visitor(0.1)])
        order, personal = result.orders.values()
        self.assertAlmostEqual(order.ready_at, 0.6)
        self.assertAlmostEqual(personal.preparation_started_at, 0.6)
        self.assertAlmostEqual(order.picked_up_at, 1.2)
        self.assertAlmostEqual(order.delivered_at, 8.7)
        metrics = summarize(result)
        times = metrics["completed_delivery_minutes"]
        self.assertAlmostEqual(times["mean"], 8.7)
        self.assertAlmostEqual(times["mean_preparation"], 0.6)
        self.assertAlmostEqual(times["mean_courier_wait"], 0.6)
        self.assertAlmostEqual(times["mean_outbound_travel"], 7.5)
        self.assertAlmostEqual(times["mean"], sum(times[k] for k in (
            "mean_queue_wait", "mean_preparation", "mean_courier_wait", "mean_outbound_travel")))
        self.assertEqual(metrics["undelivered_rate"], 0)

    def test_visitor_does_not_wait_or_return_for_later_order(self):
        result = run_simulation(SimulationConfig(), [visitor(0), delivery(0.1)])
        self.assertEqual(summarize(result)["pending_by_stage"]["awaiting_courier"], 1)
        self.assertEqual(next(iter(result.couriers.values())).delivery_order_ids, ())

    def test_nonparticipant_does_not_deliver(self):
        result = run_simulation(SimulationConfig(), [delivery(0), visitor(0.1, False)])
        self.assertEqual(summarize(result)["completed_deliveries"], 0)

    def test_one_order_per_person_and_oldest_ready_first(self):
        result = run_simulation(SimulationConfig(), [
            delivery(0), delivery(0.1), visitor(0.2), visitor(0.3)])
        couriers = list(result.couriers.values())
        self.assertEqual(couriers[0].delivery_order_ids, ("order-1",))
        self.assertEqual(couriers[1].delivery_order_ids, ("order-2",))
        self.assertEqual(summarize(result)["completed_deliveries"], 2)

    def test_observation_end_keeps_in_transit_order_pending(self):
        result = run_simulation(SimulationConfig(duration_minutes=2),
                                [delivery(0), visitor(0.1)])
        metrics = summarize(result)
        self.assertEqual(metrics["pending_by_stage"]["in_transit"], 1)
        self.assertIsNone(metrics["completed_delivery_minutes"]["mean"])
        self.assertIsNone(result.orders["order-1"].delivered_at)

    def test_pending_stages_account_for_all_unfinished_orders(self):
        result = run_simulation(SimulationConfig(duration_minutes=0.9),
                                [delivery(0), delivery(0.1), delivery(0.2)])
        metrics = summarize(result)
        self.assertEqual(metrics["pending_by_stage"], {
            "queued": 1, "preparing": 1, "awaiting_courier": 1, "in_transit": 0})
        self.assertEqual(sum(metrics["pending_by_stage"].values()), metrics["undelivered_orders"])

    def test_stores_have_independent_queues_and_matching(self):
        config = SimulationConfig(stores=(StoreConfig(id="a"), StoreConfig(id="b")))
        result = run_simulation(config, [delivery(0, "a"), visitor(0, store="b")])
        self.assertEqual([o.ready_at for o in result.orders.values()], [0.6, 0.6])
        self.assertEqual(summarize(result)["completed_deliveries"], 0)

    def test_completion_at_observation_end_counts_as_completed(self):
        config = SimulationConfig(duration_minutes=1.2, round_trip_minutes=0)
        result = run_simulation(config, [delivery(0), visitor(0.1)])
        self.assertEqual(summarize(result)["completed_deliveries"], 1)

    def test_empty_scenario_has_no_undefined_numeric_outputs(self):
        config = SimulationConfig(stores=(StoreConfig(delivery_orders_per_hour=0, visitors_per_hour=0),))
        metrics = summarize(run_simulation(config))
        self.assertEqual(metrics["delivery_orders"], 0)
        self.assertIsNone(metrics["undelivered_rate"])

    def test_random_generation_and_results_are_reproducible(self):
        config = SimulationConfig()
        self.assertEqual(generate_arrivals(config), generate_arrivals(config))
        first, second = run_simulation(config), run_simulation(config)
        self.assertEqual(first.orders, second.orders)
        metrics = summarize(first)
        self.assertEqual(metrics["delivery_orders"],
                         metrics["completed_deliveries"] + metrics["undelivered_orders"])
        for order in first.orders.values():
            if order.delivered_at is not None:
                self.assertLessEqual(order.ordered_at, order.preparation_started_at)
                self.assertLessEqual(order.preparation_started_at, order.ready_at)
                self.assertLessEqual(order.ready_at, order.picked_up_at)
                self.assertLessEqual(order.picked_up_at, order.delivered_at)

    def test_invalid_configuration_is_rejected(self):
        for kwargs in ({"participation_rate": 1.1}, {"duration_minutes": 0},
                       {"round_trip_minutes": -1}, {"duration_minutes": float("nan")},
                       {"stores": ()}, {"stores": (StoreConfig(), StoreConfig())}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                SimulationConfig(**kwargs)
        with self.assertRaises(ValueError):
            StoreConfig(orders_per_hour=0)


if __name__ == "__main__":
    unittest.main()
