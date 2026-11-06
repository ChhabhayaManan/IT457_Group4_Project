"""Quick check that a deployment answers correctly. Standard library only.

Usage:
    python infra/scripts/smoke_test.py http://<alb-dns-name> [--calls 20]
    python infra/scripts/smoke_test.py "$(terraform -chdir=infra output -raw alb_url)"

Exits 0 when every endpoint answers as expected, 1 otherwise. Also prints
which instances answered, so with more than one server you can see the
load balancer spreading requests.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections import Counter

EXPECTED_STATUS = "Match live, stream available"


def get_json(url: str, timeout: float = 10.0) -> tuple[int, dict, dict]:
    """(status, headers, body); status 0 and an error body when the call fails."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, dict(response.headers), json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), {"error": str(error)}
    except (OSError, ValueError) as error:
        return 0, {}, {"error": str(error)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base_url")
    parser.add_argument("--calls", type=int, default=20, help="requests to / for the instance spread")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    ok = True

    status, _, body = get_json(f"{base}/")
    if status == 200 and body.get("status") == EXPECTED_STATUS:
        print(f"PASS  GET /        -> {body}")
    else:
        print(f"FAIL  GET /        -> {status} {body}")
        ok = False

    status, headers, body = get_json(f"{base}/score")
    cache = headers.get("Cache-Control") or headers.get("cache-control")
    if status == 200 and "score" in body:
        print(f"PASS  GET /score   -> {body.get('score')} (Cache-Control: {cache})")
    else:
        print(f"FAIL  GET /score   -> {status} {body}")
        ok = False

    status, _, body = get_json(f"{base}/health")
    if status == 200 and body == {"status": "ok"}:
        print("PASS  GET /health")
    else:
        print(f"FAIL  GET /health  -> {status} {body}")
        ok = False

    seen = Counter()
    for _ in range(args.calls):
        _, _, body = get_json(f"{base}/")
        seen[body.get("instance", "?")] += 1
    print(f"Instances answering {args.calls} calls to /: {dict(seen)}")

    print("SMOKE TEST PASSED" if ok else "SMOKE TEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
