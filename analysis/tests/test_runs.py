import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from make_dummy_data import make_dummy_data  # noqa: E402
from plot_latency_vs_instances import collect_e1, plot  # noqa: E402
from runs import load_runs  # noqa: E402


def test_dummy_data_is_marked(tmp_path):
    make_dummy_data(str(tmp_path))
    runs = load_runs(str(tmp_path))
    assert runs, "dummy generator wrote no runs"
    assert all(run.meta["dummy"] is True for run in runs)


def test_load_runs_skips_folders_without_meta(tmp_path):
    (tmp_path / "not-a-run").mkdir()
    make_dummy_data(str(tmp_path))
    names = {run.name for run in load_runs(str(tmp_path))}
    assert "not-a-run" not in names


def test_collect_e1_median_and_range(tmp_path):
    for run, p95 in [(1, 100.0), (2, 300.0), (3, 200.0)]:
        folder = tmp_path / f"e1-n2-r{run}"
        folder.mkdir()
        (folder / "meta.json").write_text(json.dumps({"experiment": "e1", "variant": "n2", "run": run}))
        (folder / "run_summary.csv").write_text(
            "endpoint,requests,errors,error_rate,duration_s,rps,p50_ms,p95_ms,p99_ms\n"
            f"ALL,10,0,0.0,1,10,50,{p95},400\n"
        )
    rows = collect_e1(load_runs(str(tmp_path)), endpoint="ALL")
    assert rows == [{
        "instances": 2, "runs": 3,
        "p50_median": 50.0, "p50_min": 50.0, "p50_max": 50.0,
        "p95_median": 200.0, "p95_min": 100.0, "p95_max": 300.0,
    }]


def test_plot_writes_png(tmp_path):
    make_dummy_data(str(tmp_path / "data"))
    out = tmp_path / "e1.png"
    plot(str(tmp_path / "data"), str(out), endpoint="ALL")
    assert out.stat().st_size > 1000
