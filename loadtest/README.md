# Load tests (k6)

| Script | Experiment | Shape |
| --- | --- | --- |
| `constant_rate.js` | E1, E4 | same rate for a fixed time (`RATE`, `DURATION`) |
| `spike.js` | E2, E3 | baseline → 10× in 30 s → hold → back down (`BASELINE_RATE`, `SPIKE_RATE`, `*_MIN`) |
| `overload.js` | E5 | rate above E1's limit, panic mode off vs on (`RATE`, `DURATION`) |

All scripts share `lib/journey.js`. `MIX` picks what one iteration does: `journey`
(`/` → `/score` → `/play` → `/home`, the default), or a single endpoint (`score`, `play`,
`home`, `root`). Every request is tagged `name=<endpoint>`.

## Run names

`<experiment>-<variant>-r<run>`, for example:

| Run name | Meaning |
| --- | --- |
| `e1-n4-r2` | E1, fixed size 4 instances, second run |
| `e2-step-r1` | E2, step scaling, first run |
| `e3-prewarm-r3` | E3, pre-warmed, third run |
| `e4-cdn-r1` / `e4-direct-r1` | E4 through CloudFront / straight to the ALB |
| `e5-panicoff-r1` / `e5-panicon-r1` | E5 with panic mode off / on |

E1 runs five times per size (`r1`–`r5`), the other experiments three times (`r1`–`r3`);
the report uses the median and range.

## Output

`run.sh` runs on the k6 box and uploads to `s3://<results bucket>/runs/<run name>/`:

| File | In git? | Content |
| --- | --- | --- |
| `per_second.csv` | yes, under `analysis/data/<run name>/` | `timestamp,t,endpoint,requests,errors,p50_ms,p95_ms,p99_ms` |
| `run_summary.csv` | yes | whole run per endpoint: `endpoint,requests,errors,error_rate,duration_s,rps,p50_ms,p95_ms,p99_ms` |
| `meta.json` | yes | experiment, variant, run, start, end (unix seconds) |
| `summary.json` | yes | k6 end-of-test summary |
| `raw.csv.gz` | no (too big) | every k6 sample |

`errors` counts requests with status 0 (no response) or ≥ 400. `endpoint` is `ALL` for
all requests in that second together.

## Quick local check

Run the app locally (see `app/`), then:

```bash
k6 run -e BASE_URL=http://localhost:8000 -e RATE=5 -e DURATION=10s loadtest/constant_rate.js
k6 run -e BASE_URL=http://localhost:8000 -e UNIT=s -e BASELINE_RATE=2 -e SPIKE_RATE=10 loadtest/spike.js
python loadtest/aggregate.py raw.csv.gz -o per_second.csv -s run_summary.csv
```
