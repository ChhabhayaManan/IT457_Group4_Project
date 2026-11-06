"""Find out which server is answering, so load tests can show requests spreading out."""

import os
import socket
import urllib.request

IMDS_URL = "http://169.254.169.254"


def get_instance_id(imds_url: str = IMDS_URL, timeout: float = 1.0) -> str:
    """EC2 instance ID from the metadata service (IMDSv2).

    INSTANCE_ID in the environment wins (handy locally). Off EC2 the metadata
    call fails fast and the hostname is used instead.
    """
    override = os.environ.get("INSTANCE_ID")
    if override:
        return override
    try:
        token_request = urllib.request.Request(
            f"{imds_url}/latest/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        with urllib.request.urlopen(token_request, timeout=timeout) as response:
            token = response.read().decode()
        id_request = urllib.request.Request(
            f"{imds_url}/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token},
        )
        with urllib.request.urlopen(id_request, timeout=timeout) as response:
            return response.read().decode()
    except OSError:
        return socket.gethostname()
