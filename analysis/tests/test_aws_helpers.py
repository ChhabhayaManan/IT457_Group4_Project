import os
import shlex
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "loadtest"))

from pull_cloudwatch import rows_from_results  # noqa: E402
from start_run import build_command, run_name  # noqa: E402


def test_run_name():
    assert run_name("e1", "n4", 2) == "e1-n4-r2"


def test_build_command_fetches_run_sh_then_runs_it():
    command = build_command("my-bucket", "e1", "n4", 2, "constant_rate.js", "http://alb.example", ["-e", "RATE=50"])
    first, second = command.split(" && ")
    assert first == "aws s3 cp s3://my-bucket/scripts/run.sh /opt/loadtest/run.sh"
    assert shlex.split(second) == [
        "bash", "/opt/loadtest/run.sh", "e1", "n4", "2", "constant_rate.js",
        "-e", "BASE_URL=http://alb.example", "-e", "RATE=50",
    ]


def test_build_command_quotes_spaces():
    command = build_command("b", "e5", "panicon", 1, "overload.js", "http://x", ["-e", "NOTE=two words"])
    assert "NOTE=two words" in shlex.split(command.split(" && ")[1])


def test_rows_from_results_merges_by_minute():
    t0 = datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 11, 9, 10, 1, tzinfo=timezone.utc)
    results = [
        {"Id": "in_service", "Timestamps": [t1, t0], "Values": [3.0, 1.0]},
        {"Id": "alb_p95_ms", "Timestamps": [t0], "Values": [0.25]},  # seconds from CloudWatch
    ]
    rows = rows_from_results(results)
    assert rows == [
        {"timestamp": int(t0.timestamp()), "in_service": 1.0, "alb_p95_ms": 250.0},
        {"timestamp": int(t1.timestamp()), "in_service": 3.0},
    ]
