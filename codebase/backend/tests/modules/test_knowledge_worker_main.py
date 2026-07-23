from contextlib import contextmanager

from app.modules.knowledge import worker


def test_worker_main_builds_runtime_and_commits(monkeypatch) -> None:
    from app.modules.knowledge import worker_main

    calls: list[object] = []

    class FakeSession:
        def commit(self) -> None:
            calls.append("commit")

    @contextmanager
    def fake_runtime():
        calls.append("open")
        yield FakeSession(), object(), object()
        calls.append("close")

    monkeypatch.setattr(worker_main, "worker_runtime", fake_runtime)
    monkeypatch.setattr(
        worker,
        "sync_pending_documents",
        lambda db, storage, adapter, limit: calls.append(
            (db, storage, adapter, limit)
        )
        or worker.WorkerResult(uploaded=1, refreshed=2, failed=0),
    )

    assert worker_main.main(["--limit", "25"]) == 0
    assert calls[0] == "open"
    assert calls[1][3] == 25
    assert calls[2:] == ["commit", "close"]


def test_worker_main_rejects_missing_runtime_settings(monkeypatch) -> None:
    from app.modules.knowledge import worker_main

    for name in (
        "POSTGRES_DSN",
        "MINIO_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "MINIO_BUCKET",
        "RAGFLOW_BASE_URL",
        "RAGFLOW_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    try:
        with worker_main.worker_runtime():
            raise AssertionError("runtime must not start")
    except RuntimeError as exc:
        assert str(exc) == "missing worker settings: POSTGRES_DSN, MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, RAGFLOW_BASE_URL, RAGFLOW_API_KEY"
