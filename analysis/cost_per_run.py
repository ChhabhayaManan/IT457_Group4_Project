"""Cost per run and per million requests.

    python infra/scripts/cost_report.py --start 2026-11-06 --end 2026-11-16 -o analysis/costs.csv
    python analysis/cost_per_run.py [analysis/data] --costs analysis/costs.csv -o analysis/cost.csv

Two views, because AWS bills by the day, not by the run:
  est_app_*  app servers only, for this run: instance-minutes from
             cloudwatch.csv x the on-demand hourly price (--hourly-price).
             An estimate (c7i-flex.large has no CPU credits, so no extra charge on top).
  day_*      everything the project was billed that UTC day (from costs.csv:
             EC2, ALB, NAT, CloudFront, S3 ...) shared over all the
             requests sent that day. The real number, including idle time.
"""

import argparse

import pandas as pd

from runs import Run, load_runs

# c7i-flex.large, Linux, on-demand, ap-south-1 (AWS Pricing API, Nov 2026).
APP_HOURLY_USD = 0.0848


def _requests(run: Run) -> float:
    summary = run.summary
    if summary is None:
        return float("nan")
    row = summary[summary["endpoint"] == "ALL"]
    return float(row["requests"].iloc[0]) if not row.empty else float("nan")


def _instance_minutes(run: Run) -> float:
    cloudwatch = run.cloudwatch
    if cloudwatch is None or cloudwatch.empty:
        return float("nan")
    inside = cloudwatch[(cloudwatch["timestamp"] >= run.meta["start"]) & (cloudwatch["timestamp"] < run.meta["end"])]
    return float(inside["in_service"].sum(min_count=1))  # one row per minute; NaN if the ASG metric is missing


def cost_table(runs: list[Run], costs_path: str, hourly_price: float = APP_HOURLY_USD) -> pd.DataFrame:
    rows = []
    for run in runs:
        if "start" not in run.meta:
            continue
        minutes = _instance_minutes(run)
        requests = _requests(run)
        est = minutes / 60 * hourly_price
        rows.append({
            "run": run.name,
            "experiment": run.meta.get("experiment"),
            "variant": run.meta.get("variant"),
            "date": pd.to_datetime(run.meta["start"], unit="s", utc=True).strftime("%Y-%m-%d"),
            "requests": requests,
            "instance_minutes": minutes,
            "est_app_usd": est,
            "est_app_usd_per_million": est / requests * 1e6 if requests else float("nan"),
            "dummy": run.is_dummy,
        })
    table = pd.DataFrame(rows)
    if table.empty:
        return table

    costs = pd.read_csv(costs_path)
    day_usd = costs.groupby("date")["usd"].sum().rename("day_usd")
    day_requests = table.groupby("date")["requests"].sum().rename("day_requests")
    table = table.join(day_usd, on="date").join(day_requests, on="date")
    table["day_usd_per_million"] = table["day_usd"] / table["day_requests"] * 1e6
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("data_dir", nargs="?", default="analysis/data")
    parser.add_argument("--costs", default="analysis/costs.csv", help="output of infra/scripts/cost_report.py")
    parser.add_argument("--hourly-price", type=float, default=APP_HOURLY_USD)
    parser.add_argument("-o", "--out", default="analysis/cost.csv")
    args = parser.parse_args()
    table = cost_table(load_runs(args.data_dir), args.costs, args.hourly_price)
    if table.empty:
        raise SystemExit(f"no runs in {args.data_dir}")
    if table["dummy"].any():
        print("WARNING: dummy runs included; do not use this table in the report")
    table.round(4).to_csv(args.out, index=False)
    print(table[["run", "requests", "est_app_usd", "day_usd_per_million"]].round(4).to_string(index=False))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
