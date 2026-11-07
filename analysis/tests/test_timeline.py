import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from make_dummy_data import make_dummy_data  # noqa: E402
from plot_timeline import plot, timeline_frame  # noqa: E402
from runs import load_runs  # noqa: E402


def _run(tmp_path, name):
    make_dummy_data(str(tmp_path))
    return next(r for r in load_runs(str(tmp_path)) if r.name == name)


def test_timeline_frame_aligns_instances_to_every_second(tmp_path):
    frame = timeline_frame(_run(tmp_path, "e2-step-r1"))
    assert list(frame.columns) == ["t", "p95_ms", "errors", "in_service"]
    assert frame["in_service"].isna().sum() == 0  # CloudWatch minutes carried forward
    assert frame["t"].is_monotonic_increasing


def test_timeline_frame_without_cloudwatch(tmp_path):
    run = _run(tmp_path, "e2-step-r1")
    os.remove(os.path.join(run.path, "cloudwatch.csv"))
    frame = timeline_frame(run)
    assert frame["in_service"].isna().all()


def test_plot_two_runs(tmp_path):
    make_dummy_data(str(tmp_path / "data"))
    out = tmp_path / "timeline.png"
    plot([str(tmp_path / "data" / "e2-step-r1"), str(tmp_path / "data" / "e3-prewarm-r1")], str(out))
    assert out.stat().st_size > 1000
