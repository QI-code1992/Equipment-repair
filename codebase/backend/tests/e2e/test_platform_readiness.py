import os
from urllib.request import urlopen

import pytest


def test_task011_https_healthz_live_stack() -> None:
    base_url = os.getenv("TASK011_LIVE_HTTPS_URL")
    if not base_url:
        pytest.skip("TASK-011 live-stack environment is not configured")

    with urlopen(f"{base_url.rstrip('/')}/healthz", timeout=10) as response:
        assert response.status == 200
