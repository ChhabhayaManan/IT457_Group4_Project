import csv
import gzip
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aggregate import aggregate, percentile  # noqa: E402

HEADER = "metric_name,timestamp,metric_value,check,error,error_code,expected_response,group,method,name,proto,scenario,service,status,subproto,tls_version,url,extra_tags,metadata"


def row(metric, ts, value, name, status):
    return f"{metric},{ts},{value},,,,true,,GET,{name},HTTP/1.1,constant,,{status},,,{name},,"


def write_raw(path, rows):
    with gzip.open(path, "wt", newline="") as f:
        f.write(HEADER + "\n" + "\n".join(rows) + "\n")


def read_out(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def test_percentile_interpolates():
    assert percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.5
    assert percentile([10.0], 95) == 10.0


def test_groups_by_second_and_endpoint(tmp_path):
    raw = tmp_path / "raw.csv.gz"
    write_raw(raw, [
        row("http_req_duration", 100, 10.0, "play", 200),
        row("http_req_duration", 100, 30.0, "play", 200),
        row("http_req_duration", 100, 2.0, "score", 200),
        row("http_reqs", 100, 1, "play", 200),  # other metrics are ignored
        row("http_req_duration", 101, 20.0, "play", 200),
    ])
    out = tmp_path / "per_second.csv"
    aggregate(str(raw), str(out))
    rows = read_out(out)
    play_100 = next(r for r in rows if r["t"] == "0" and r["endpoint"] == "play")
    assert play_100["timestamp"] == "100"
    assert play_100["requests"] == "2"
    assert float(play_100["p50_ms"]) == 20.0
    all_100 = next(r for r in rows if r["t"] == "0" and r["endpoint"] == "ALL")
    assert all_100["requests"] == "3"
    assert {r["t"] for r in rows} == {"0", "1"}


def test_failed_requests_count_as_errors(tmp_path):
    raw = tmp_path / "raw.csv.gz"
    write_raw(raw, [
        row("http_req_duration", 200, 5.0, "play", 200),
        row("http_req_duration", 200, 0.0, "play", 0),  # connection refused / timeout
        row("http_req_duration", 200, 900.0, "play", 503),
    ])
    out = tmp_path / "per_second.csv"
    aggregate(str(raw), str(out))
    play = next(r for r in read_out(out) if r["endpoint"] == "play")
    assert play["requests"] == "3"
    assert play["errors"] == "2"


def test_empty_input_writes_header_only(tmp_path):
    raw = tmp_path / "raw.csv.gz"
    write_raw(raw, [])
    out = tmp_path / "per_second.csv"
    aggregate(str(raw), str(out))
    assert read_out(out) == []


def test_run_summary_uses_every_sample(tmp_path):
    raw = tmp_path / "raw.csv.gz"
    write_raw(raw, [
        row("http_req_duration", 300, 10.0, "play", 200),
        row("http_req_duration", 300, 20.0, "play", 200),
        row("http_req_duration", 301, 30.0, "play", 200),
        row("http_req_duration", 301, 40.0, "play", 500),
    ])
    summary = tmp_path / "run_summary.csv"
    aggregate(str(raw), str(tmp_path / "per_second.csv"), str(summary))
    play = next(r for r in read_out(summary) if r["endpoint"] == "play")
    assert play["requests"] == "4"
    assert play["errors"] == "1"
    assert float(play["error_rate"]) == 0.25
    assert float(play["p50_ms"]) == 25.0
    assert play["duration_s"] == "2"
