"""Measure how long one new app server takes to start serving traffic.

    python app/scripts/measure_boot.py [--runs 3]

This time is the floor for reactive scaling: no policy can add capacity faster
than a server boots. It adds one instance to the group, times each stage, and
puts the group back:
  request -> EC2 launch -> ASG InService -> healthy in the target group

Run it with scaling_mode = "step" (so max is above the current size) and no
load test running. Needs AWS credentials.
"""

import argparse
import sys
import time
from datetime import datetime, timezone

POLL_SECONDS = 2


def new_instance_ids(before: set[str], group: dict) -> list[str]:
    return [i["InstanceId"] for i in group["Instances"] if i["InstanceId"] not in before]


def boot_timings(requested: datetime, launched: datetime, in_service: datetime, healthy: datetime) -> dict:
    def seconds(a, b):
        return round((b - a).total_seconds(), 1)

    return {
        "request_to_launch_s": seconds(requested, launched),
        "launch_to_in_service_s": seconds(launched, in_service),
        "in_service_to_healthy_s": seconds(in_service, healthy),
        "request_to_healthy_s": seconds(requested, healthy),
    }


def now() -> datetime:
    return datetime.now(timezone.utc)


def measure_once(autoscaling, ec2, elb, asg_name: str, tg_arn: str) -> dict:
    group = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])["AutoScalingGroups"][0]
    desired, maximum = group["DesiredCapacity"], group["MaxSize"]
    if desired >= maximum:
        sys.exit(f"group is at its max ({maximum}); apply with scaling_mode = \"step\" first")
    before = {i["InstanceId"] for i in group["Instances"]}

    requested = now()
    autoscaling.set_desired_capacity(AutoScalingGroupName=asg_name, DesiredCapacity=desired + 1, HonorCooldown=False)
    try:
        instance_id, in_service = None, None
        while in_service is None:
            time.sleep(POLL_SECONDS)
            group = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])["AutoScalingGroups"][0]
            new = new_instance_ids(before, group)
            if new:
                instance_id = new[0]
                state = next(i for i in group["Instances"] if i["InstanceId"] == instance_id)["LifecycleState"]
                if state == "InService":
                    in_service = now()
        launched = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]["LaunchTime"]

        healthy = None
        while healthy is None:
            health = elb.describe_target_health(TargetGroupArn=tg_arn, Targets=[{"Id": instance_id, "Port": 8000}])
            if health["TargetHealthDescriptions"][0]["TargetHealth"]["State"] == "healthy":
                healthy = now()
            else:
                time.sleep(POLL_SECONDS)
    finally:
        autoscaling.set_desired_capacity(AutoScalingGroupName=asg_name, DesiredCapacity=desired, HonorCooldown=False)

    result = boot_timings(requested, launched, in_service, healthy)
    result["instance_id"] = instance_id
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default="group4-hotstar")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()

    import boto3

    autoscaling = boto3.client("autoscaling", region_name=args.region)
    ec2 = boto3.client("ec2", region_name=args.region)
    elb = boto3.client("elbv2", region_name=args.region)
    tg_arn = elb.describe_target_groups(Names=[f"{args.project}-app"])["TargetGroups"][0]["TargetGroupArn"]

    for run in range(1, args.runs + 1):
        result = measure_once(autoscaling, ec2, elb, f"{args.project}-app", tg_arn)
        print(f"run {run}: {result}")
        if run < args.runs:
            print("waiting 120 s for the extra instance to drain...")
            time.sleep(120)


if __name__ == "__main__":
    main()
