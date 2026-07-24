from app.integrations.file_scanning.clamav import ClamAvScanner, ScannerUnavailable


class FakeSocket:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.sent = bytearray()

    def __enter__(self) -> "FakeSocket":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def sendall(self, value: bytes) -> None:
        self.sent.extend(value)

    def recv(self, size: int) -> bytes:
        del size
        response, self.response = self.response, b""
        return response


def test_clean_stream_uses_bounded_clamav_protocol() -> None:
    connection = FakeSocket(b"stream: OK\0")
    scanner = ClamAvScanner(
        host="clamav", port=3310, timeout_seconds=2.0,
        socket_factory=lambda *args, **kwargs: connection,
    )

    assert scanner.is_safe(b"safe") is True
    assert connection.sent == b"zINSTREAM\0\x00\x00\x00\x04safe\x00\x00\x00\x00"


def test_infected_stream_is_rejected() -> None:
    connection = FakeSocket(b"stream: Eicar-Signature FOUND\0")
    scanner = ClamAvScanner(
        host="clamav", port=3310, timeout_seconds=2.0,
        socket_factory=lambda *args, **kwargs: connection,
    )

    assert scanner.is_safe(b"unsafe") is False


def test_unknown_or_unreachable_scanner_fails_closed() -> None:
    connection = FakeSocket(b"unexpected response\0")
    scanner = ClamAvScanner(
        host="clamav", port=3310, timeout_seconds=2.0,
        socket_factory=lambda *args, **kwargs: connection,
    )

    try:
        scanner.is_safe(b"content")
    except ScannerUnavailable:
        pass
    else:
        raise AssertionError("unknown scanner response was accepted")
