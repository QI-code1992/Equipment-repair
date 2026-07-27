from __future__ import annotations

import os
import socket
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def main() -> None:
    base_url = os.environ["RAGFLOW_BASE_URL"].rstrip("/")
    api_key = os.environ["RAGFLOW_API_KEY"]
    timeout = float(os.environ["RAGFLOW_TIMEOUT_SECONDS"])
    target = urlparse(base_url)
    if target.scheme not in {"http", "https"} or not target.hostname or timeout <= 0:
        raise RuntimeError("invalid RAGFlow API settings")

    port = target.port or (443 if target.scheme == "https" else 80)
    socket.getaddrinfo(target.hostname, port, type=socket.SOCK_STREAM)
    request = Request(
        f"{base_url}/api/v1/datasets",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(
                f"RAGFlow connectivity probe returned HTTP {response.status}"
            )


if __name__ == "__main__":
    main()
