"""Every graph for the final report, in one go.

    python analysis/make_figures.py [analysis/data] -o docs/figures

  e1_latency_vs_instances.png  E1  p50/p95 against 1, 2, 3 servers
  e2_e3_timeline.png           E2/E3  p95 and instance count over time, step vs pre-warm
  e4_cdn_vs_direct.png         E4  /score p95 through CloudFront vs straight to the ALB
  e5_panic_mode.png            E5  p95 and error rate with panic mode off vs on

A graph whose runs are missing is skipped (with a note), so this works as
the experiments come in. Bars show the median of the runs, whiskers the range.
"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import plot_latency_vs_instances  # noqa: E402
import plot_timeline  # noqa: E402
from runs import load_runs  # noqa: E402
from summarize import summarize  # noqa: E402


LABELS = {"direct": "straight to ALB", "cdn": "through CloudFront", "panicoff": "panic off", "panicon": "panic on"}


def _stamp_dummy(fig, rows) -> None:
    if rows["dummy"].any():
        fig.text(0.5, 0.5, "DUMMY DATA", fontsize=40, color="red", alpha=0.25, ha="center", va="center", rotation=20)


def _bars(ax, rows, variants: list[str], endpoints: list[str], metric: str, scale: float = 1.0) -> None:
    width = 0.8 / len(variants)
    for i, variant in enumerate(variants):
        medians, low, high = [], [], []
        for endpoint in endpoints:
            row = rows[(rows["variant"] == variant) & (rows["endpoint"] == endpoint)]
            if row.empty:
                medians.append(0.0), low.append(0.0), high.append(0.0)
                continue
            median = row[f"{metric}_median"].iloc[0] * scale
            medians.append(median)
            low.append(median - row[f"{metric}_min"].iloc[0] * scale)
            high.append(row[f"{metric}_max"].iloc[0] * scale - median)
        positions = [x + (i - (len(variants) - 1) / 2) * width for x in range(len(endpoints))]
        bars = ax.bar(positions, medians, width, yerr=[low, high], capsize=4, label=LABELS.get(variant, variant))
        ax.bar_label(bars, fmt="%.0f" if scale == 1.0 else "%.1f", padding=2, fontsize=8)
    ax.set_xticks(range(len(endpoints)), [f"/{e}" if e != "ALL" else "all" for e in endpoints])
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()


def figure_e4(table, out_path: str) -> bool:
    rows = table[(table["experiment"] == "e4") & (table["endpoint"] == "score")]
    if not {"direct", "cdn"} <= set(rows["variant"]):
        return False
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    _bars(ax, rows, ["direct", "cdn"], ["score"], "p95")
    ax.set_ylabel("p95 response time (ms)")
    ax.set_title("E4: /score, ALB vs CloudFront\n(5 s cache, same request rate)")
    _stamp_dummy(fig, rows)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def figure_e5(table, out_path: str) -> bool:
    rows = table[table["experiment"] == "e5"]
    if not {"panicoff", "panicon"} <= set(rows["variant"]):
        return False
    endpoints = [e for e in ["home", "play", "ALL"] if e in set(rows["endpoint"])]
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4.5))
    _bars(left, rows, ["panicoff", "panicon"], endpoints, "p95")
    left.set_ylabel("p95 response time (ms)")
    left.set_title("p95 under overload")
    _bars(right, rows, ["panicoff", "panicon"], endpoints, "error_rate", scale=100.0)
    right.set_ylabel("failed requests (%)")
    right.set_title("error rate under overload")
    fig.suptitle("E5: panic mode off vs on (same overload, same servers)")
    _stamp_dummy(fig, rows)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def make_figures(data_dir: str, out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    runs = load_runs(data_dir)
    table = summarize(runs)
    written = []

    def done(name: str, ok: bool) -> None:
        path = os.path.join(out_dir, name)
        if ok:
            written.append(path)
            print(f"wrote {path}")
        else:
            print(f"skipped {name}: runs missing")

    path = os.path.join(out_dir, "e1_latency_vs_instances.png")
    has_e1 = bool(plot_latency_vs_instances.collect_e1(runs))
    if has_e1:
        plot_latency_vs_instances.plot(data_dir, path)
    done("e1_latency_vs_instances.png", has_e1)

    spikes = [r.path for r in runs if r.meta.get("experiment") in ("e2", "e3")
              and r.meta.get("run") == 1 and r.per_second is not None]
    if spikes:
        plot_timeline.plot(sorted(spikes), os.path.join(out_dir, "e2_e3_timeline.png"))
    done("e2_e3_timeline.png", bool(spikes))

    done("e4_cdn_vs_direct.png", figure_e4(table, os.path.join(out_dir, "e4_cdn_vs_direct.png")))
    done("e5_panic_mode.png", figure_e5(table, os.path.join(out_dir, "e5_panic_mode.png")))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("data_dir", nargs="?", default="analysis/data")
    parser.add_argument("-o", "--out", default="docs/figures")
    args = parser.parse_args()
    make_figures(args.data_dir, args.out)


if __name__ == "__main__":
    main()
