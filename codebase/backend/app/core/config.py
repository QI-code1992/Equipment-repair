from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    postgres_dsn: str | None
    redis_url: str | None
    service_name: str | None = "equipment-operations-platform"
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None
    minio_secure: bool = False
    clamav_host: str | None = None
    clamav_port: int = 3310
    file_scan_timeout_seconds: float = 10.0
    ragflow_base_url: str | None = None
    ragflow_api_key: str | None = None
    ragflow_timeout_seconds: float = 30.0

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            postgres_dsn=os.getenv("POSTGRES_DSN"),
            redis_url=os.getenv("REDIS_URL"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY"),
            minio_bucket=os.getenv("MINIO_BUCKET"),
            minio_secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            clamav_host=os.getenv("CLAMAV_HOST"),
            clamav_port=int(os.getenv("CLAMAV_PORT", "3310")),
            file_scan_timeout_seconds=float(
                os.getenv("FILE_SCAN_TIMEOUT_SECONDS", "10")
            ),
            ragflow_base_url=os.getenv("RAGFLOW_BASE_URL"),
            ragflow_api_key=os.getenv("RAGFLOW_API_KEY"),
            ragflow_timeout_seconds=float(os.getenv("RAGFLOW_TIMEOUT_SECONDS", "30")),
        )
