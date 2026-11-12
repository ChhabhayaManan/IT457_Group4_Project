"""Daily AWS cost of this project, from Cost Explorer, by service.

    python infra/scripts/cost_report.py --start 2026-11-06 --end 2026-11-16 -o analysis/costs.csv

Counts only resources tagged Project=group4-hotstar (every resource gets it
from default_tags in providers.tf) and leaves out credits and refunds, so the
numbers show what the experiments really cost even when credits pay for them.
--end is exclusive. Writes date,service,usd.

One-time setup (payer account): Billing -> Cost allocation tags -> activate
"Project". Tags only count from activation on, and Cost Explorer data lags
up to 24 hours. Cost Explorer API calls cost $0.01 each.
"""

import argparse
import csv
import sys

FIELDS = ["date", "service", "usd"]


def build_request(start: str, end: str, project: str) -> dict:
    return {
        "TimePeriod": {"Start": start, "End": end},
        "Granularity": "DAILY",
        "Metrics": ["UnblendedCost"],
        "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        "Filter": {"And": [
            {"Tags": {"Key": "Project", "Values": [project], "MatchOptions": ["EQUALS"]}},
            {"Not": {"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Credit", "Refund"]}}},
        ]},
    }


def rows_from_response(response: dict) -> list[dict]:
    rows = []
    for day in response["ResultsByTime"]:
        for group in day["Groups"]:
            usd = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if usd >= 0.0001:
                rows.append({"date": day["TimePeriod"]["Start"], "service": group["Keys"][0], "usd": round(usd, 4)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD, exclusive")
    parser.add_argument("--project", default="group4-hotstar")
    parser.add_argument("-o", "--out", default="costs.csv")
    args = parser.parse_args()

    import boto3

    explorer = boto3.client("ce", region_name="us-east-1")  # Cost Explorer lives in us-east-1
    request = build_request(args.start, args.end, args.project)
    rows = []
    while True:
        response = explorer.get_cost_and_usage(**request)
        rows.extend(rows_from_response(response))
        token = response.get("NextPageToken")
        if not token:
            break
        request["NextPageToken"] = token

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    total = sum(r["usd"] for r in rows)
    by_service: dict[str, float] = {}
    for row in rows:
        by_service[row["service"]] = by_service.get(row["service"], 0.0) + row["usd"]
    for service, usd in sorted(by_service.items(), key=lambda item: -item[1]):
        print(f"  {usd:9.4f}  {service}")
    print(f"  {total:9.4f}  TOTAL (USD, before credits) -> {args.out}")
    if not rows:
        print("no tagged cost yet: is the Project tag activated, and has 24 h passed?", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
