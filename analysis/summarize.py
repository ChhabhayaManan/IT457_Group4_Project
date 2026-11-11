"""Summary table across repeated runs: median and range per experiment/variant/endpoint.

    python analysis/summarize.py [analysis/data] -o analysis/summary.csv

Each experiment variant is run 3 times; the report quotes the median and
the lowest-highest range, never a single run. Columns:
  experiment, variant, endpoint, runs, dummy,
  <m>_median, <m>_min, <m>_max for m in p50, p95, p99 (ms), error_rate, rps
"""

import argparse

import pandas as pd

from runs import Run, load_runs

METRICS = ["p50_ms", "p95_ms", "p99_ms", "error_rate", "rps"]
KEYS = ["experiment", "variant", "endpoint"]


def summarize(runs: list[Run]) -> pd.DataFrame:
    frames = []
    for run in runs:
        summary = run.summary
        if summary is None:
            continue
        summary = summary.copy()
        summary["experiment"] = run.meta.get("experiment")
        summary["variant"] = str(run.meta.get("variant"))
        summary["dummy"] = run.is_dummy
        frames.append(summary)
    if not frames:
        return pd.DataFrame(columns=KEYS + ["runs", "dummy"])

    every = pd.concat(frames, ignore_index=True)
    grouped = every.groupby(KEYS, sort=True)
    table = grouped.size().rename("runs").to_frame()
    table["dummy"] = grouped["dummy"].any()
    for metric in METRICS:
        name = metric.removesuffix("_ms")  # p95_ms -> p95_median, p95_min, p95_max
        table[f"{name}_median"] = grouped[metric].median()
        table[f"{name}_min"] = grouped[metric].min()
        table[f"{name}_max"] = grouped[metric].max()
    return table.reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("data_dir", nargs="?", default="analysis/data")
    parser.add_argument("-o", "--out", default="analysis/summary.csv")
    args = parser.parse_args()
    table = summarize(load_runs(args.data_dir))
    if table.empty:
        raise SystemExit(f"no runs with run_summary.csv in {args.data_dir}")
    if table["dummy"].any():
        print("WARNING: dummy runs included; do not use this table in the report")
    table.round(3).to_csv(args.out, index=False)
    print(f"wrote {len(table)} rows to {args.out}")


if __name__ == "__main__":
    main()
