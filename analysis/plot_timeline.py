"""E2/E3 graph: latency and instance count over time.

    python analysis/plot_timeline.py analysis/data/e2-step-r1 [analysis/data/e3-prewarm-r1] -o docs/figures/e2_e3_timeline.png

One panel per run, stacked with the same time axis: p95 latency (10 s rolling
median, left axis), errors per second, and in-service instances from
CloudWatch (right axis). With E2 and E3 together, the gap where reactive
scaling lags the spike is easy to compare.
"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import NullFormatter, ScalarFormatter  # noqa: E402

from runs import Run  # noqa: E402


def load_run(path: str) -> Run:
    import json

    with open(os.path.join(path, "meta.json")) as f:
        return Run(name=os.path.basename(os.path.normpath(path)), path=path, meta=json.load(f))


def timeline_frame(run: Run, endpoint: str = "ALL") -> pd.DataFrame:
    """One row per second: t, p95_ms, errors, in_service (NaN without cloudwatch.csv)."""
    per_second = run.per_second
    if per_second is None:
        raise SystemExit(f"{run.path} has no per_second.csv")
    frame = per_second[per_second["endpoint"] == endpoint][["timestamp", "t", "p95_ms", "errors"]].sort_values("t")

    cloudwatch = run.cloudwatch
    if cloudwatch is None or cloudwatch.empty:
        frame["in_service"] = float("nan")
    else:
        minutes = cloudwatch[["timestamp", "in_service"]].sort_values("timestamp")
        frame = pd.merge_asof(frame, minutes, on="timestamp", direction="backward")
        frame["in_service"] = frame["in_service"].bfill()
    return frame[["t", "p95_ms", "errors", "in_service"]].reset_index(drop=True)


def plot(run_paths: list[str], out_path: str, endpoint: str = "ALL") -> None:
    runs = [load_run(p) for p in run_paths]
    # Same axes on every panel, so E2 and E3 compare at a glance.
    fig, axes = plt.subplots(len(runs), 1, figsize=(10, 3.6 * len(runs)), sharex=True, sharey=True, squeeze=False)

    for ax, run in zip(axes[:, 0], runs):
        frame = timeline_frame(run, endpoint)
        minutes = frame["t"] / 60
        ax.plot(minutes, frame["p95_ms"].rolling(10, min_periods=1).median(), color="tab:orange", label="p95 latency")
        ax.set_ylabel("p95 (ms, log scale)")
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(ScalarFormatter())
        ax.yaxis.set_minor_formatter(NullFormatter())
        errors = frame["errors"] > 0
        if errors.any():
            ax.scatter(minutes[errors], frame["p95_ms"][errors], s=6, color="tab:red", label="seconds with errors")

        right = ax.twinx()
        right.step(minutes, frame["in_service"], where="post", color="tab:blue", label="in-service instances")
        right.set_ylabel("instances")
        right.set_ylim(0, 11)

        ax.set_title(f"{run.name} ({endpoint})")
        ax.grid(True, alpha=0.3)
        lines = ax.get_legend_handles_labels()
        more = right.get_legend_handles_labels()
        ax.legend(lines[0] + more[0], lines[1] + more[1], loc="upper right", fontsize=8)
        if run.is_dummy:
            ax.text(0.5, 0.5, "DUMMY DATA", transform=ax.transAxes, fontsize=30, color="red", alpha=0.25,
                    ha="center", va="center", rotation=15)

    axes[-1, 0].set_xlabel("minutes since test start")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", help="run folders, e.g. analysis/data/e2-step-r1")
    parser.add_argument("-o", "--out", default="timeline.png")
    parser.add_argument("--endpoint", default="ALL")
    args = parser.parse_args()
    plot(args.runs, args.out, args.endpoint)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
