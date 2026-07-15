from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    postgres_dsn: str | None
    redis_url: str | None
    service_name: str | None = "equipment-operations-platform"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            postgres_dsn=os.getenv("POSTGRES_DSN"),
            redis_url=os.getenv("REDIS_URL"),
        )
    service_name: str = "equipment-operations-platform"
