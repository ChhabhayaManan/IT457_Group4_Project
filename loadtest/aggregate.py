"""Turn k6's raw CSV output into small summary files.

    python3 aggregate.py raw.csv.gz -o per_second.csv [-s run_summary.csv]

Standard library only and streaming, so it runs on the k6 box right after a
test (a 30-minute spike is millions of raw rows) and only the small summaries
are downloaded. Works on Python 3.9+.

per_second.csv: timestamp,t,endpoint,requests,errors,p50_ms,p95_ms,p99_ms
  timestamp  unix second (to line up with CloudWatch)
  t          seconds since the first request of the run
  endpoint   the k6 "name" tag (root, score, play, home) or ALL
  errors     requests with status 0 (no response) or >= 400

run_summary.csv: endpoint,requests,errors,error_rate,duration_s,rps,p50_ms,p95_ms,p99_ms
  the same numbers over the whole run, computed from every sample
  (percentiles cannot be rebuilt from per-second percentiles).
"""

import argparse
import csv
import gzip
from collections import defaultdict

FIELDS = ["timestamp", "t", "endpoint", "requests", "errors", "p50_ms", "p95_ms", "p99_ms"]
SUMMARY_FIELDS = ["endpoint", "requests", "errors", "error_rate", "duration_s", "rps", "p50_ms", "p95_ms", "p99_ms"]


def percentile(sorted_values, q):
    """Linear interpolation between closest ranks (same as numpy's default)."""
    if not sorted_values:
        return 0.0
    position = (len(sorted_values) - 1) * q / 100.0
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def is_error(status):
    try:
        code = int(float(status))
    except ValueError:
        return True
    return code == 0 or code >= 400


def aggregate(raw_path, out_path, summary_path=None):
    durations = defaultdict(list)  # (second, endpoint) -> [ms, ...]
    errors = defaultdict(int)

    opener = gzip.open if raw_path.endswith(".gz") else open
    with opener(raw_path, "rt", newline="") as f:
        for record in csv.DictReader(f):
            if record["metric_name"] != "http_req_duration":
                continue
            second = int(float(record["timestamp"]))
            value = float(record["metric_value"])
            failed = is_error(record["status"])
            for endpoint in (record["name"] or "unnamed", "ALL"):
                durations[(second, endpoint)].append(value)
                if failed:
                    errors[(second, endpoint)] += 1

    seconds = [second for second, _ in durations]
    start = min(seconds, default=0)
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        for (second, endpoint) in sorted(durations):
            values = sorted(durations[(second, endpoint)])
            writer.writerow([
                second,
                second - start,
                endpoint,
                len(values),
                errors[(second, endpoint)],
                round(percentile(values, 50), 2),
                round(percentile(values, 95), 2),
                round(percentile(values, 99), 2),
            ])

    if summary_path:
        duration_s = (max(seconds) - start + 1) if seconds else 0
        whole_run = defaultdict(list)
        whole_errors = defaultdict(int)
        for (second, endpoint), values in durations.items():
            whole_run[endpoint].extend(values)
            whole_errors[endpoint] += errors[(second, endpoint)]
        with open(summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(SUMMARY_FIELDS)
            for endpoint in sorted(whole_run):
                values = sorted(whole_run[endpoint])
                writer.writerow([
                    endpoint,
                    len(values),
                    whole_errors[endpoint],
                    round(whole_errors[endpoint] / len(values), 4),
                    duration_s,
                    round(len(values) / duration_s, 2),
                    round(percentile(values, 50), 2),
                    round(percentile(values, 95), 2),
                    round(percentile(values, 99), 2),
                ])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("raw", help="k6 --out csv file (.csv or .csv.gz)")
    parser.add_argument("-o", "--out", default="per_second.csv")
    parser.add_argument("-s", "--summary", default=None, help="also write whole-run summary here")
    args = parser.parse_args()
    aggregate(args.raw, args.out, args.summary)
    print(f"wrote {args.out}" + (f" and {args.summary}" if args.summary else ""))


if __name__ == "__main__":
    main()
