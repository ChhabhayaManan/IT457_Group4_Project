"""Panic mode: Hotstar's switch that turns off non-critical features under overload.

On AWS the flag lives in SSM Parameter Store (PANIC_PARAM) and is re-read every
few seconds, so it can be flipped without a redeploy. Locally there is no
parameter and the PANIC_MODE environment variable is used instead.
"""

import logging
import os
import threading
import time

log = logging.getLogger("panic")


class PanicFlag:
    def __init__(self, param: str | None, client=None, poll_seconds: float = 5.0, region: str | None = None):
        self.param = param
        self.client = client
        self.poll_seconds = poll_seconds
        self.region = region
        self._on = False

    @classmethod
    def from_env(cls) -> "PanicFlag":
        return cls(
            param=os.environ.get("PANIC_PARAM") or None,
            poll_seconds=float(os.environ.get("PANIC_POLL_SECONDS", "5")),
            region=os.environ.get("AWS_REGION"),
        )

    def is_on(self) -> bool:
        if self.param is None:
            return os.environ.get("PANIC_MODE", "off").strip().lower() == "on"
        return self._on

    def refresh(self) -> None:
        """Read the parameter once. Any failure keeps the last known value."""
        try:
            if self.client is None:
                import boto3  # only needed on AWS

                self.client = boto3.client("ssm", region_name=self.region)
            value = self.client.get_parameter(Name=self.param)["Parameter"]["Value"]
            self._on = value.strip().lower() == "on"
        except Exception as error:  # throttling, no credentials, network: never crash the app
            log.warning("panic flag read failed, keeping %s: %s", self._on, error)

    def start(self) -> None:
        """Poll in a background thread. Does nothing without a parameter."""
        if self.param is None:
            return

        def loop():
            while True:
                self.refresh()
                time.sleep(self.poll_seconds)

        threading.Thread(target=loop, daemon=True, name="panic-flag").start()
