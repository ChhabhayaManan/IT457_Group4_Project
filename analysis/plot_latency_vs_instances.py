"""E1 graph: response time against instance count (course deliverable 3).

    python analysis/plot_latency_vs_instances.py [analysis/data] -o docs/figures/e1_latency_vs_instances.png

Uses every e1-n<count>-r<run> folder. Each point is the median of the runs at
that count; the bar shows the lowest and highest run.
"""

import argparse
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from runs import Run, load_runs  # noqa: E402


def collect_e1(runs: list[Run], endpoint: str = "ALL") -> list[dict]:
    by_count: dict[int, list[tuple[float, float]]] = {}
    for run in runs:
        if run.meta.get("experiment") != "e1" or run.summary is None:
            continue
        count = int(str(run.meta["variant"]).lstrip("n"))
        row = run.summary[run.summary["endpoint"] == endpoint]
        if row.empty:
            continue
        by_count.setdefault(count, []).append((float(row["p50_ms"].iloc[0]), float(row["p95_ms"].iloc[0])))

    rows = []
    for count in sorted(by_count):
        p50s = [p50 for p50, _ in by_count[count]]
        p95s = [p95 for _, p95 in by_count[count]]
        rows.append({
            "instances": count, "runs": len(p50s),
            "p50_median": statistics.median(p50s), "p50_min": min(p50s), "p50_max": max(p50s),
            "p95_median": statistics.median(p95s), "p95_min": min(p95s), "p95_max": max(p95s),
        })
    return rows


def plot(data_dir: str, out_path: str, endpoint: str = "ALL") -> None:
    runs = load_runs(data_dir)
    rows = collect_e1(runs, endpoint)
    if not rows:
        raise SystemExit(f"no e1 runs with a run_summary.csv in {data_dir}")

    counts = [r["instances"] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for key, label, marker in (("p50", "p50 (median request)", "o"), ("p95", "p95 (slowest 5%)", "s")):
        medians = [r[f"{key}_median"] for r in rows]
        low = [r[f"{key}_median"] - r[f"{key}_min"] for r in rows]
        high = [r[f"{key}_max"] - r[f"{key}_median"] for r in rows]
        ax.errorbar(counts, medians, yerr=[low, high], marker=marker, capsize=4, label=label)

    ax.set_xscale("log", base=2)
    ax.set_xticks(counts, [str(c) for c in counts])
    ax.set_xlabel("Instances behind the load balancer")
    ax.set_ylabel("Response time (ms)")
    ax.set_title(f"E1: response time vs instance count ({endpoint}, same request rate)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    if any(run.is_dummy for run in runs):
        fig.text(0.5, 0.5, "DUMMY DATA", fontsize=40, color="red", alpha=0.25, ha="center", va="center", rotation=20)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("data_dir", nargs="?", default="analysis/data")
    parser.add_argument("-o", "--out", default="e1_latency_vs_instances.png")
    parser.add_argument("--endpoint", default="ALL", help="ALL, root, score, play or home")
    args = parser.parse_args()
    plot(args.data_dir, args.out, args.endpoint)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
