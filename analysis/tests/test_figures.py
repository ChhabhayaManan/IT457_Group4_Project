import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from make_dummy_data import make_dummy_data  # noqa: E402
from make_figures import make_figures  # noqa: E402


def test_make_figures_writes_every_graph(tmp_path):
    make_dummy_data(str(tmp_path / "data"))
    written = make_figures(str(tmp_path / "data"), str(tmp_path / "figures"))
    names = sorted(os.path.basename(p) for p in written)
    assert names == [
        "e1_latency_vs_instances.png",
        "e2_e3_timeline.png",
        "e4_cdn_vs_direct.png",
        "e5_panic_mode.png",
    ]
    for path in written:
        assert os.path.getsize(path) > 1000


def test_make_figures_skips_missing_experiments(tmp_path):
    make_dummy_data(str(tmp_path / "data"))
    for name in os.listdir(tmp_path / "data"):
        if not name.startswith("e1-"):
            for f in os.listdir(tmp_path / "data" / name):
                os.remove(tmp_path / "data" / name / f)
            os.rmdir(tmp_path / "data" / name)
    written = make_figures(str(tmp_path / "data"), str(tmp_path / "figures"))
    assert [os.path.basename(p) for p in written] == ["e1_latency_vs_instances.png"]
