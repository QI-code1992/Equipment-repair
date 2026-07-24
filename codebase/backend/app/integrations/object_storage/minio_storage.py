from io import BytesIO
from pathlib import PurePosixPath
from typing import Protocol
from uuid import uuid4

class MinioClient(Protocol):
    def put_object(self, **kwargs: object) -> object: ...

    def get_object(self, bucket_name: str, object_name: str) -> object: ...

    def remove_object(self, bucket_name: str, object_name: str) -> None: ...


class MinioObjectStorage:
    def __init__(self, *, client: MinioClient, bucket_name: str) -> None:
        if not bucket_name or "/" in bucket_name or ".." in bucket_name:
            raise ValueError("valid bucket name is required")
        self.client = client
        self.bucket_name = bucket_name

    def put(self, *, filename: str, content: bytes, content_type: str) -> str:
        suffix = PurePosixPath(filename).suffix.lower()
        object_key = f"knowledge/{uuid4().hex}{suffix}"
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_key,
            data=BytesIO(content),
            length=len(content),
            content_type=content_type,
        )
        return object_key

    def get(self, object_key: str) -> bytes:
        self._validate_key(object_key)
        response = self.client.get_object(self.bucket_name, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, object_key: str) -> None:
        self._validate_key(object_key)
        self.client.remove_object(self.bucket_name, object_key)

    @staticmethod
    def _validate_key(object_key: str) -> None:
        path = PurePosixPath(object_key)
        if (
            not object_key.startswith("knowledge/")
            or path.is_absolute()
            or ".." in path.parts
            or len(path.parts) != 2
        ):
            raise ValueError("invalid object key")


def build_minio_storage(
    *,
    endpoint: str,
    access_key: str,
    secret_key: str,
    bucket_name: str,
    secure: bool,
) -> MinioObjectStorage:
    from minio import Minio

    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )
    return MinioObjectStorage(client=client, bucket_name=bucket_name)
