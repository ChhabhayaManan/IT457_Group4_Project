import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from measure_boot import boot_timings, new_instance_ids  # noqa: E402


def test_new_instance_ids_ignores_old_ones():
    group = {"Instances": [{"InstanceId": "i-old"}, {"InstanceId": "i-new"}]}
    assert new_instance_ids({"i-old"}, group) == ["i-new"]


def test_boot_timings_in_seconds():
    clicked = datetime(2026, 11, 9, 10, 0, 0, tzinfo=timezone.utc)
    timings = boot_timings(
        requested=clicked,
        launched=clicked + timedelta(seconds=8),
        in_service=clicked + timedelta(seconds=40),
        healthy=clicked + timedelta(seconds=95),
    )
    assert timings == {
        "request_to_launch_s": 8.0,
        "launch_to_in_service_s": 32.0,
        "in_service_to_healthy_s": 55.0,
        "request_to_healthy_s": 95.0,
    }
