import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runs import load_runs  # noqa: E402
from summarize import summarize  # noqa: E402

HEADER = "endpoint,requests,errors,error_rate,duration_s,rps,p50_ms,p95_ms,p99_ms\n"


def _run(tmp_path, name, experiment, variant, rows, dummy=False):
    folder = tmp_path / name
    folder.mkdir()
    meta = {"experiment": experiment, "variant": variant, "run": int(name[-1])}
    if dummy:
        meta["dummy"] = True
    (folder / "meta.json").write_text(json.dumps(meta))
    (folder / "run_summary.csv").write_text(HEADER + "".join(rows))


def test_summarize_groups_runs_by_experiment_variant_endpoint(tmp_path):
    _run(tmp_path, "e1-n2-r1", "e1", "n2", ["ALL,100,1,0.01,10,10,40,100,200\n", "play,50,1,0.02,10,5,60,150,250\n"])
    _run(tmp_path, "e1-n2-r2", "e1", "n2", ["ALL,100,3,0.03,10,10,50,300,400\n"])
    _run(tmp_path, "e1-n2-r3", "e1", "n2", ["ALL,100,2,0.02,10,10,45,200,300\n"])
    _run(tmp_path, "e1-n4-r1", "e1", "n4", ["ALL,100,0,0.0,10,10,20,50,90\n"])

    table = summarize(load_runs(str(tmp_path)))
    row = table[(table["variant"] == "n2") & (table["endpoint"] == "ALL")].iloc[0]
    assert row["runs"] == 3
    assert row["p95_median"] == 200.0
    assert row["p95_min"] == 100.0
    assert row["p95_max"] == 300.0
    assert row["error_rate_median"] == 0.02
    assert row["dummy"] == False  # noqa: E712
    assert len(table) == 3  # n2/ALL, n2/play, n4/ALL


def test_summarize_flags_dummy(tmp_path):
    _run(tmp_path, "e1-n1-r1", "e1", "n1", ["ALL,1,0,0.0,1,1,1,1,1\n"], dummy=True)
    assert bool(summarize(load_runs(str(tmp_path)))["dummy"].iloc[0]) is True
