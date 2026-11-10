"""JSON 条件で実行し、集計と注文・来店者の記録を出力する CLI。"""
import argparse
import csv
from dataclasses import asdict, fields
import json
from pathlib import Path
from campus_delivery_sim.analysis.metrics import summarize
from campus_delivery_sim.config import SimulationConfig
from campus_delivery_sim.models.courier import Courier
from campus_delivery_sim.models.order import Order
from campus_delivery_sim.simulation.engine import run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description="大学内フードデリバリーのシミュレーション")
    parser.add_argument("--config", type=Path, help="JSON 条件ファイル。省略時は初期設定")
    parser.add_argument("--output", type=Path, help="結果の出力ディレクトリ")
    args = parser.parse_args()
    try:
        config = SimulationConfig.from_json(args.config) if args.config else SimulationConfig()
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        parser.error(f"設定を読み込めません: {exc}")
    result = run_simulation(config)
    summary = summarize(result)
    rendered = json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "summary.json").write_text(rendered + "\n", encoding="utf-8")
        (args.output / "config.json").write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for name, model, records in (("orders", Order, result.orders.values()),
                                      ("visitors", Courier, result.couriers.values())):
            with (args.output / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=[f.name for f in fields(model)])
                writer.writeheader()
                writer.writerows(asdict(record) for record in records)
    print(rendered)


if __name__ == "__main__":
    main()
