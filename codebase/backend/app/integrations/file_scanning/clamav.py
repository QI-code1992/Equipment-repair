import socket
from collections.abc import Callable
from pathlib import Path
from struct import pack
from typing import Protocol


class ScannerUnavailable(RuntimeError):
    pass


class ScannerSocket(Protocol):
    def __enter__(self) -> "ScannerSocket": ...

    def __exit__(self, *args: object) -> None: ...

    def sendall(self, value: bytes) -> None: ...

    def recv(self, size: int) -> bytes: ...


class ClamAvScanner:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        timeout_seconds: float,
        socket_factory: Callable[..., ScannerSocket] = socket.create_connection,
    ) -> None:
        if not host or not 1 <= port <= 65535 or timeout_seconds <= 0:
            raise ValueError("valid ClamAV settings are required")
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds
        self.socket_factory = socket_factory

    def is_safe(self, content: bytes) -> bool:
        return self._scan_chunks(
            (content[offset : offset + 64 * 1024] for offset in range(0, len(content), 64 * 1024))
        )

    def is_safe_file(self, path: Path) -> bool:
        with path.open("rb") as source:
            return self._scan_chunks(iter(lambda: source.read(64 * 1024), b""))

    def _scan_chunks(self, chunks) -> bool:
        try:
            with self.socket_factory(
                (self.host, self.port), timeout=self.timeout_seconds
            ) as connection:
                connection.sendall(b"zINSTREAM\0")
                for chunk in chunks:
                    connection.sendall(pack("!I", len(chunk)) + chunk)
                connection.sendall(pack("!I", 0))
                response = self._response(connection)
        except OSError as error:
            raise ScannerUnavailable("file scanner is unavailable") from error
        if response.endswith(" OK"):
            return True
        if response.endswith(" FOUND"):
            return False
        raise ScannerUnavailable("file scanner returned an invalid response")

    @staticmethod
    def _response(connection: ScannerSocket) -> str:
        response = bytearray()
        while len(response) <= 4096:
            chunk = connection.recv(1024)
            if not chunk:
                break
            response.extend(chunk)
            if b"\0" in chunk:
                break
        if b"\0" not in response:
            raise ScannerUnavailable("file scanner response was incomplete")
        return bytes(response).split(b"\0", 1)[0].decode("utf-8", errors="replace")
