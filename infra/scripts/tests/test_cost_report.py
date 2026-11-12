import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cost_report import build_request, rows_from_response  # noqa: E402


def test_build_request_filters_project_tag_and_drops_credits():
    request = build_request("2026-11-06", "2026-11-16", "group4-hotstar")
    assert request["TimePeriod"] == {"Start": "2026-11-06", "End": "2026-11-16"}
    assert request["Granularity"] == "DAILY"
    tag, not_credits = request["Filter"]["And"]
    assert tag == {"Tags": {"Key": "Project", "Values": ["group4-hotstar"], "MatchOptions": ["EQUALS"]}}
    assert set(not_credits["Not"]["Dimensions"]["Values"]) == {"Credit", "Refund"}


def test_rows_from_response_skips_zero_cost():
    response = {"ResultsByTime": [
        {"TimePeriod": {"Start": "2026-11-09"}, "Groups": [
            {"Keys": ["Amazon Elastic Compute Cloud - Compute"], "Metrics": {"UnblendedCost": {"Amount": "1.2345"}}},
            {"Keys": ["AWS Key Management Service"], "Metrics": {"UnblendedCost": {"Amount": "0.0000001"}}},
        ]},
    ]}
    assert rows_from_response(response) == [
        {"date": "2026-11-09", "service": "Amazon Elastic Compute Cloud - Compute", "usd": 1.2345},
    ]
