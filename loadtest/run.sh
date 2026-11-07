#!/bin/bash
# Runs ON the k6 box (Session Manager shell, or started by start_run.py).
#
#   bash /opt/loadtest/run.sh <experiment> <variant> <run> <script> [k6 args...]
#   bash /opt/loadtest/run.sh e1 n3 1 constant_rate.js -e BASE_URL=http://<alb> -e RATE=250
#
# Run name = <experiment>-<variant>-r<run>, e.g. e1-n4-r1. Results land in
# s3://$RESULTS_BUCKET/runs/<run name>/:
#   raw.csv.gz      every k6 sample (large, stays in S3)
#   per_second.csv  one row per second per endpoint (small, goes into git)
#   run_summary.csv whole-run numbers per endpoint (small, goes into git)
#   summary.json    k6 end-of-test summary
#   meta.json       experiment, variant, run, start, end
#   k6.log          console output
set -euo pipefail

if [ "$#" -lt 4 ]; then
  echo "usage: $0 <experiment> <variant> <run> <script> [k6 args...]" >&2
  exit 2
fi

EXPERIMENT="$1"
VARIANT="$2"
RUN_NUMBER="$3"
SCRIPT="$4"
shift 4
RUN_NAME="${EXPERIMENT}-${VARIANT}-r${RUN_NUMBER}"

# shellcheck disable=SC1091
source /etc/loadgen.env
WORK=/opt/loadtest
OUT="/opt/results/${RUN_NAME}"

# Always run the latest scripts uploaded by terraform apply.
aws s3 sync "s3://${RESULTS_BUCKET}/scripts/" "${WORK}/" --delete --only-show-errors
mkdir -p "$OUT"
ulimit -n 250000

START=$(date +%s)
echo "RUN ${RUN_NAME} START ${START}"
# k6 exits non-zero when a threshold fails; we still want the results uploaded.
set +e
k6 run --out "csv=${OUT}/raw.csv.gz" --summary-export "${OUT}/summary.json" "$@" "${WORK}/${SCRIPT}" 2>&1 | tee "${OUT}/k6.log"
K6_EXIT=${PIPESTATUS[0]}
set -e
END=$(date +%s)
echo "RUN ${RUN_NAME} END ${END} (k6 exit ${K6_EXIT})"

printf '{"experiment": "%s", "variant": "%s", "run": %s, "run_name": "%s", "script": "%s", "start": %s, "end": %s, "k6_exit": %s}\n' \
  "$EXPERIMENT" "$VARIANT" "$RUN_NUMBER" "$RUN_NAME" "$SCRIPT" "$START" "$END" "$K6_EXIT" > "${OUT}/meta.json"

python3 "${WORK}/aggregate.py" "${OUT}/raw.csv.gz" -o "${OUT}/per_second.csv" -s "${OUT}/run_summary.csv"
aws s3 cp --recursive --only-show-errors "$OUT" "s3://${RESULTS_BUCKET}/runs/${RUN_NAME}/"
echo "UPLOADED s3://${RESULTS_BUCKET}/runs/${RUN_NAME}/"
