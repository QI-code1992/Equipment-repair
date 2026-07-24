from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
INFRA_ROOT = REPOSITORY_ROOT / "codebase" / "infra"


def test_task005_validation_stack_has_migration_and_isolated_services() -> None:
    compose = (INFRA_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    env_example = (INFRA_ROOT / ".env.example").read_text(encoding="utf-8")
    api_service = compose.split("  worker:", maxsplit=1)[0]

    for service in ("migrate:", "worker:", "minio:", "clamav:", "validator:"):
        assert service in compose
    assert compose.count("profiles: [validation]") == 5
    assert "api:\n    build:" in compose
    assert "RAGFLOW_BASE_URL: ${RAGFLOW_BASE_URL}" in api_service
    assert "RAGFLOW_API_KEY: ${RAGFLOW_API_KEY}" in api_service
    assert "RAGFLOW_TIMEOUT_SECONDS: ${RAGFLOW_TIMEOUT_SECONDS}" in api_service
    assert 'extra_hosts:\n      - "host.docker.internal:host-gateway"' in api_service
    assert "networks: [platform, ragflow-egress]" in api_service
    assert "RAGFLOW_TIMEOUT_SECONDS=30" in env_example
    assert "target: test" in compose
    assert "condition: service_completed_successfully" in compose
    assert "ragflow-egress" in compose
    assert "internal: true" in compose
    assert "test_task005_postgres.py" in compose
    assert "TASK005_ALLOW_DESTRUCTIVE_TESTS: \"1\"" in compose
    assert '["python", "-m", "app.modules.knowledge.worker_main", "--poll-seconds", "1"]' in compose


def test_task005_validation_scripts_use_host_api_url_and_cleanup() -> None:
    invoke = (INFRA_ROOT / "task-005" / "scripts" / "Invoke-Validation.ps1").read_text(
        encoding="utf-8"
    )
    create_environment = (
        INFRA_ROOT / "task-005" / "scripts" / "New-ValidationEnvironment.ps1"
    ).read_text(encoding="utf-8")
    remove_environment = (
        INFRA_ROOT / "task-005" / "scripts" / "Remove-ValidationEnvironment.ps1"
    ).read_text(encoding="utf-8")

    assert "Convert-ToHostUrl" in invoke
    assert "TASK005_RAGFLOW_DATASET_ID" in invoke
    assert '-e "TASK005_RAGFLOW_DATASET_ID=$datasetId"' in invoke
    assert "RAGFLOW_TIMEOUT_SECONDS" in invoke
    assert "$apiRagflowProbe" in invoke
    assert "docker @compose exec -T api python -c $apiRagflowProbe" in invoke
    assert "socket.getaddrinfo" in invoke
    assert "/api/v1/datasets" in invoke
    assert "run --rm --no-deps --build" in invoke
    assert "down --volumes --remove-orphans" in invoke
    assert "run --rm --no-deps worker python -c" in invoke
    assert "make_bucket" in invoke
    assert "New-RandomHex" in create_environment
    assert "icacls" in create_environment
    assert "POSTGRES_DB=equipment_task5_validation_live" in create_environment
    assert "RAGFLOW_TIMEOUT_SECONDS=30" in create_environment
    assert "GetTempPath" in remove_environment
    assert "Remove-Item" in remove_environment
    assert "task005-validation-marker" in remove_environment
    assert "equipment-task005-" in remove_environment
    assert "--profile validation" in remove_environment
    live_test = (REPOSITORY_ROOT / "codebase" / "backend" / "tests" / "integration" / "test_task005_live_stack.py").read_text(encoding="utf-8")
    assert "worker_main.main" not in live_test
    assert "TASK005_VALIDATION_ENVIRONMENT" in create_environment
    assert "catch" in create_environment
    assert "$cleanupFailure" in remove_environment
    assert "if ($cleanupFailure)" in remove_environment
