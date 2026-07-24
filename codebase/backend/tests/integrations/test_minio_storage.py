from app.integrations.object_storage.minio_storage import MinioObjectStorage


class FakeMinioClient:
    def __init__(self) -> None:
        self.put_calls: list[dict[str, object]] = []
        self.get_payload = b"stored content"
        self.removed: tuple[str, str] | None = None

    def put_object(self, **kwargs: object) -> None:
        self.put_calls.append(kwargs)

    def get_object(self, bucket_name: str, object_name: str) -> object:
        class Response:
            def __init__(self, payload: bytes) -> None:
                self.payload = payload
                self.closed = False
                self.released = False

            def read(self) -> bytes:
                return self.payload

            def close(self) -> None:
                self.closed = True

            def release_conn(self) -> None:
                self.released = True

        return Response(self.get_payload)

    def remove_object(self, bucket_name: str, object_name: str) -> None:
        self.removed = (bucket_name, object_name)


def test_put_uses_generated_key_and_exact_metadata() -> None:
    client = FakeMinioClient()
    storage = MinioObjectStorage(client=client, bucket_name="knowledge")

    object_key = storage.put(
        filename="manual.pdf",
        content=b"pdf-content",
        content_type="application/pdf",
    )

    assert object_key.startswith("knowledge/")
    assert object_key.endswith(".pdf")
    assert "manual.pdf" not in object_key
    call = client.put_calls[0]
    assert call["bucket_name"] == "knowledge"
    assert call["object_name"] == object_key
    assert call["length"] == 11
    assert call["content_type"] == "application/pdf"
    assert call["data"].read() == b"pdf-content"


def test_get_and_delete_stay_within_configured_bucket() -> None:
    client = FakeMinioClient()
    storage = MinioObjectStorage(client=client, bucket_name="knowledge")

    assert storage.get("knowledge/abc.txt") == b"stored content"
    storage.delete("knowledge/abc.txt")

    assert client.removed == ("knowledge", "knowledge/abc.txt")


def test_rejects_untrusted_object_key() -> None:
    storage = MinioObjectStorage(client=FakeMinioClient(), bucket_name="knowledge")

    for key in ("../secret", "/absolute", "other/abc.txt", "knowledge/../secret"):
        try:
            storage.get(key)
        except ValueError as error:
            assert str(error) == "invalid object key"
        else:
            raise AssertionError(f"unsafe key accepted: {key}")
