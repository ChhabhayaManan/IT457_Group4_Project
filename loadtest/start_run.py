"""Start a k6 run on the load generator from your laptop, wait, and fetch the results.

    python loadtest/start_run.py e1 n3 1 constant_rate.js -e RATE=250 -e DURATION=15m
    python loadtest/start_run.py e4 cdn 1 constant_rate.js --target cdn -e MIX=score -e RATE=800

Needs: AWS credentials, `terraform apply` done with enable_loadgen = true.
Reads loadgen_instance_id, results_bucket, alb_url and cdn_url from
`terraform -chdir=infra output -json`, sends run.sh to the k6 box through SSM
Run Command, waits for it, then downloads the small result files into
analysis/data/<run name>/ (add --raw to also fetch raw.csv.gz into
loadtest/results/raw/<run name>/, which is gitignored).
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SMALL_FILES = ["per_second.csv", "run_summary.csv", "summary.json", "meta.json", "k6.log"]


def run_name(experiment: str, variant: str, run: int) -> str:
    return f"{experiment}-{variant}-r{run}"


def build_command(bucket: str, experiment: str, variant: str, run: int, script: str,
                  base_url: str, k6_args: list[str]) -> str:
    """Shell command for the k6 box: fetch the latest run.sh, then run it."""
    run_sh = "/opt/loadtest/run.sh"
    args = ["bash", run_sh, experiment, variant, str(run), script, "-e", f"BASE_URL={base_url}", *k6_args]
    return f"aws s3 cp s3://{bucket}/scripts/run.sh {run_sh} && " + " ".join(shlex.quote(a) for a in args)


def terraform_outputs() -> dict:
    raw = subprocess.run(["terraform", f"-chdir={os.path.join(REPO, 'infra')}", "output", "-json"],
                         check=True, capture_output=True, text=True).stdout
    return {key: value["value"] for key, value in json.loads(raw).items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("experiment", help="e1 .. e5")
    parser.add_argument("variant", help="e.g. n4, step, prewarm, cdn, direct, panicoff, panicon")
    parser.add_argument("run", type=int, help="1, 2 or 3")
    parser.add_argument("script", help="constant_rate.js, spike.js or overload.js")
    parser.add_argument("--target", choices=["alb", "cdn"], default="alb")
    parser.add_argument("--raw", action="store_true", help="also download raw.csv.gz")
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument("-e", dest="env", action="append", default=[], metavar="KEY=VALUE",
                        help="passed to k6 as -e KEY=VALUE (repeatable)")
    args = parser.parse_args()

    import boto3

    outputs = terraform_outputs()
    instance_id = outputs.get("loadgen_instance_id")
    bucket = outputs.get("results_bucket")
    base_url = outputs.get("cdn_url" if args.target == "cdn" else "alb_url")
    if not instance_id or not bucket:
        sys.exit("no load generator: apply with enable_loadgen = true first")
    if not base_url:
        sys.exit(f"no {args.target} URL in terraform outputs (CDN needs enable_cdn = true)")

    name = run_name(args.experiment, args.variant, args.run)
    k6_args = [part for pair in args.env for part in ("-e", pair)]
    command = build_command(bucket, args.experiment, args.variant, args.run, args.script, base_url, k6_args)

    ssm = boto3.client("ssm", region_name=args.region)
    sent = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [command], "executionTimeout": ["7200"]},
        Comment=name,
    )
    command_id = sent["Command"]["CommandId"]
    print(f"started {name} on {instance_id} (command {command_id}) against {base_url}")

    status = "Pending"
    while status in ("Pending", "InProgress", "Delayed"):
        time.sleep(15)
        try:
            invocation = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        except ssm.exceptions.InvocationDoesNotExist:
            continue
        status = invocation["Status"]
        print(f"  {time.strftime('%H:%M:%S')} {status}")
    print(invocation.get("StandardOutputContent", "")[-2000:])
    if status != "Success":
        print(invocation.get("StandardErrorContent", "")[-2000:], file=sys.stderr)
        return 1

    s3 = boto3.client("s3", region_name=args.region)
    data_dir = os.path.join(REPO, "analysis", "data", name)
    os.makedirs(data_dir, exist_ok=True)
    for file_name in SMALL_FILES:
        s3.download_file(bucket, f"runs/{name}/{file_name}", os.path.join(data_dir, file_name))
    print(f"results in {data_dir}")
    if args.raw:
        raw_dir = os.path.join(REPO, "loadtest", "results", "raw", name)
        os.makedirs(raw_dir, exist_ok=True)
        s3.download_file(bucket, f"runs/{name}/raw.csv.gz", os.path.join(raw_dir, "raw.csv.gz"))
        print(f"raw samples in {raw_dir}")
    print(f"next: python analysis/pull_cloudwatch.py {os.path.relpath(data_dir, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
