import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cost_per_run import cost_table  # noqa: E402
from runs import load_runs  # noqa: E402

DAY = 1_794_268_800  # 2026-11-10 00:00 UTC


def _run(tmp_path, name, start, requests, in_service):
    folder = tmp_path / name
    folder.mkdir()
    (folder / "meta.json").write_text(json.dumps(
        {"experiment": name.split("-")[0], "variant": name.split("-")[1], "run": 1, "start": start, "end": start + 600}))
    (folder / "run_summary.csv").write_text(
        "endpoint,requests,errors,error_rate,duration_s,rps,p50_ms,p95_ms,p99_ms\n"
        f"ALL,{requests},0,0.0,600,1,1,1,1\n")
    if in_service is not None:
        (folder / "cloudwatch.csv").write_text(
            "timestamp,in_service,desired,cpu_avg,alb_requests,alb_p95_ms\n"
            + "".join(f"{start + 60 * i},{n},{n},10,1,1\n" for i, n in enumerate(in_service)))


def test_cost_table(tmp_path):
    _run(tmp_path, "e2-step-r1", DAY + 3600, 1_000_000, [1, 2, 3])
    _run(tmp_path, "e3-prewarm-r1", DAY + 7200, 1_000_000, None)
    costs = tmp_path / "costs.csv"
    costs.write_text("date,service,usd\n2026-11-10,EC2,3.00\n2026-11-10,ELB,1.00\n2026-11-11,EC2,9\n")

    table = cost_table(load_runs(str(tmp_path)), str(costs), hourly_price=0.6)
    step = table[table["run"] == "e2-step-r1"].iloc[0]
    assert step["date"] == "2026-11-10"
    assert step["instance_minutes"] == 6
    assert step["est_app_usd"] == pytest.approx(0.06)  # 6 min at $0.6/h
    assert step["est_app_usd_per_million"] == pytest.approx(0.06)
    assert step["day_usd"] == 4.0
    assert step["day_requests"] == 2_000_000
    assert step["day_usd_per_million"] == 2.0

    prewarm = table[table["run"] == "e3-prewarm-r1"].iloc[0]
    assert prewarm["instance_minutes"] != prewarm["instance_minutes"]  # NaN without cloudwatch.csv
