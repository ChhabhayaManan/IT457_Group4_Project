"""Write FAKE run folders so the plot scripts can be built before real runs exist.

    python analysis/make_dummy_data.py <out dir>     (never analysis/data)

Every meta.json says "dummy": true and every plot made from it is stamped
DUMMY DATA. Never commit this output or use it in the report.
"""

import argparse
import csv
import json
import os
import random

SUMMARY_FIELDS = ["endpoint", "requests", "errors", "error_rate", "duration_s", "rps", "p50_ms", "p95_ms", "p99_ms"]
PER_SECOND_FIELDS = ["timestamp", "t", "endpoint", "requests", "errors", "p50_ms", "p95_ms", "p99_ms"]
CLOUDWATCH_FIELDS = ["timestamp", "in_service", "desired", "cpu_avg", "alb_requests", "alb_p95_ms"]
START = 1_800_000_000


def _write_csv(path: str, fields: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)


def _meta(folder: str, experiment: str, variant: str, run: int, end: int) -> None:
    meta = {"experiment": experiment, "variant": variant, "run": run, "run_name": os.path.basename(folder),
            "start": START, "end": end, "dummy": True}
    with open(os.path.join(folder, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


def _e1(out_dir: str, rng: random.Random) -> None:
    for instances in (1, 2, 3):
        for run in (1, 2, 3, 4, 5):
            folder = os.path.join(out_dir, f"e1-n{instances}-r{run}")
            os.makedirs(folder, exist_ok=True)
            p50 = 20 + 400 / instances * rng.uniform(0.9, 1.1)
            p95 = 40 + 1600 / instances * rng.uniform(0.85, 1.15)
            _write_csv(os.path.join(folder, "run_summary.csv"), SUMMARY_FIELDS,
                       [["ALL", 900000, 0, 0.0, 900, 1000, round(p50, 2), round(p95, 2), round(p95 * 1.4, 2)]])
            _meta(folder, "e1", f"n{instances}", run, START + 900)


def _spike(out_dir: str, experiment: str, variant: str, prewarm: bool, rng: random.Random) -> None:
    duration = 31 * 60
    folder = os.path.join(out_dir, f"{experiment}-{variant}-r1")
    os.makedirs(folder, exist_ok=True)
    per_second, cloudwatch = [], []
    capacity = 6.0 if prewarm else 1.0
    for t in range(duration):
        spiking = 300 <= t < 930
        demand = 10.0 if spiking else 1.0  # instances needed
        if t % 60 == 0:
            if demand > capacity:
                capacity = min(10.0, capacity + 1)  # +1 per minute, like the step policy
            elif not spiking and t > 1200 and capacity > 1:
                capacity -= 1
        overload = max(demand / capacity, 1.0)
        p95 = 45 * overload ** 2 * rng.uniform(0.9, 1.1)
        errors = int(max(0.0, overload - 2) * 20)
        requests = 800 if spiking else 80
        per_second.append([START + t, t, "ALL", requests, errors, round(p95 / 2, 2), round(p95, 2), round(p95 * 1.5, 2)])
        if t % 60 == 0:
            cloudwatch.append([START + t, int(capacity), int(capacity), round(min(95.0, 40 * overload), 1),
                               requests * 60, round(p95, 1)])
    _write_csv(os.path.join(folder, "per_second.csv"), PER_SECOND_FIELDS, per_second)
    _write_csv(os.path.join(folder, "cloudwatch.csv"), CLOUDWATCH_FIELDS, cloudwatch)
    _meta(folder, experiment, variant, 1, START + duration)


def make_dummy_data(out_dir: str, seed: int = 4) -> None:
    rng = random.Random(seed)
    os.makedirs(out_dir, exist_ok=True)
    _e1(out_dir, rng)
    _spike(out_dir, "e2", "step", prewarm=False, rng=rng)
    _spike(out_dir, "e3", "prewarm", prewarm=True, rng=rng)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out_dir")
    args = parser.parse_args()
    if os.path.abspath(args.out_dir).replace("\\", "/").rstrip("/").endswith("analysis/data"):
        parser.error("refusing to write dummy data into analysis/data (real results only)")
    make_dummy_data(args.out_dir)
    print(f"wrote DUMMY runs to {args.out_dir}")


if __name__ == "__main__":
    main()
