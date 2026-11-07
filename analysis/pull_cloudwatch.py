"""Fetch per-minute CloudWatch metrics for one run's time window.

    python analysis/pull_cloudwatch.py analysis/data/e2-step-r1

Reads start/end from the run's meta.json (2 minutes of padding each side) and
writes cloudwatch.csv next to it:
  timestamp,in_service,desired,cpu_avg,alb_requests,alb_p95_ms

The ASG and load balancer are found by name (project prefix group4-hotstar),
so no Terraform state is needed. Needs AWS credentials.
"""

import argparse
import csv
import json
import os
from datetime import datetime, timezone

FIELDS = ["timestamp", "in_service", "desired", "cpu_avg", "alb_requests", "alb_p95_ms"]
PAD_SECONDS = 120


def metric_queries(asg_name: str, alb_suffix: str) -> list[dict]:
    def query(query_id, namespace, metric, dimensions, stat):
        return {
            "Id": query_id,
            "MetricStat": {
                "Metric": {"Namespace": namespace, "MetricName": metric,
                           "Dimensions": [{"Name": k, "Value": v} for k, v in dimensions.items()]},
                "Period": 60,
                "Stat": stat,
            },
        }

    asg = {"AutoScalingGroupName": asg_name}
    alb = {"LoadBalancer": alb_suffix}
    return [
        query("in_service", "AWS/AutoScaling", "GroupInServiceInstances", asg, "Average"),
        query("desired", "AWS/AutoScaling", "GroupDesiredCapacity", asg, "Average"),
        query("cpu_avg", "AWS/EC2", "CPUUtilization", asg, "Average"),
        query("alb_requests", "AWS/ApplicationELB", "RequestCount", alb, "Sum"),
        query("alb_p95_ms", "AWS/ApplicationELB", "TargetResponseTime", alb, "p95"),
    ]


def rows_from_results(results: list[dict]) -> list[dict]:
    """Merge GetMetricData results into one dict per minute, sorted by time."""
    by_time: dict[int, dict] = {}
    for result in results:
        scale = 1000.0 if result["Id"] == "alb_p95_ms" else 1.0  # seconds -> ms
        for stamp, value in zip(result["Timestamps"], result["Values"]):
            key = int(stamp.timestamp())
            by_time.setdefault(key, {"timestamp": key})[result["Id"]] = value * scale
    return [by_time[key] for key in sorted(by_time)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir")
    parser.add_argument("--project", default="group4-hotstar")
    parser.add_argument("--region", default="ap-south-1")
    args = parser.parse_args()

    import boto3

    with open(os.path.join(args.run_dir, "meta.json")) as f:
        meta = json.load(f)
    start = datetime.fromtimestamp(meta["start"] - PAD_SECONDS, tz=timezone.utc)
    end = datetime.fromtimestamp(meta["end"] + PAD_SECONDS, tz=timezone.utc)

    elb = boto3.client("elbv2", region_name=args.region)
    alb_arn = elb.describe_load_balancers(Names=[f"{args.project}-alb"])["LoadBalancers"][0]["LoadBalancerArn"]
    alb_suffix = alb_arn.split(":loadbalancer/")[1]
    asg_name = f"{args.project}-app"

    cloudwatch = boto3.client("cloudwatch", region_name=args.region)
    results, token = [], None
    while True:
        kwargs = {"MetricDataQueries": metric_queries(asg_name, alb_suffix), "StartTime": start, "EndTime": end}
        if token:
            kwargs["NextToken"] = token
        page = cloudwatch.get_metric_data(**kwargs)
        results.extend(page["MetricDataResults"])
        token = page.get("NextToken")
        if not token:
            break

    # Pages can split one metric; join them before merging.
    joined: dict[str, dict] = {}
    for result in results:
        entry = joined.setdefault(result["Id"], {"Id": result["Id"], "Timestamps": [], "Values": []})
        entry["Timestamps"].extend(result["Timestamps"])
        entry["Values"].extend(result["Values"])

    rows = rows_from_results(list(joined.values()))
    out_path = os.path.join(args.run_dir, "cloudwatch.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} minutes to {out_path}")


if __name__ == "__main__":
    main()
