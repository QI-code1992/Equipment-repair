import json
from secrets import token_hex
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class UrllibRagflowTransport:
    def __init__(self, *, base_url: str, api_key: str, timeout_seconds: float) -> None:
        normalized_base_url = base_url.rstrip("/")
        parsed = urlparse(normalized_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("valid HTTP RAGFlow base URL is required")
        self.base_url = normalized_base_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def request(self, **kwargs: object) -> dict[str, object]:
        method = str(kwargs["method"])
        path = str(kwargs["path"])
        headers = {"Authorization": f"Bearer {self.api_key}"}
        body: bytes | None = None
        if "json_body" in kwargs:
            body = json.dumps(kwargs["json_body"]).encode()
            headers["Content-Type"] = "application/json"
        elif "multipart" in kwargs:
            body, content_type = self._multipart(kwargs["multipart"])
            headers["Content-Type"] = content_type
        request = Request(
            f"{self.base_url}{path}", data=body, headers=headers, method=method
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.loads(response.read())
        if not isinstance(payload, dict):
            raise ValueError("RAGFlow response must be a JSON object")
        return payload

    @staticmethod
    def _multipart(value: object) -> tuple[bytes, str]:
        if not isinstance(value, dict) or set(value) != {"file"}:
            raise ValueError("one file multipart field is required")
        file_value = value["file"]
        if not isinstance(file_value, tuple) or len(file_value) != 3:
            raise ValueError("invalid multipart file")
        filename, content, content_type = file_value
        if not isinstance(content, bytes):
            raise ValueError("multipart content must be bytes")
        boundary = f"ragflow-{token_hex(12)}"
        safe_name = str(filename).replace('"', "_").replace("\r", "_").replace("\n", "_")
        lines = [
            f"--{boundary}\r\n",
            f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n',
            f"Content-Type: {content_type}\r\n\r\n",
        ]
        body = "".join(lines).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        return body, f"multipart/form-data; boundary={boundary}"
