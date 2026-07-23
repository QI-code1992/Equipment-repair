[CmdletBinding()]
param(
    [string]$BackendPath = "codebase/backend"
)

$ErrorActionPreference = "Stop"
$required = @(
    "TASK005_POSTGRES_DSN",
    "TASK005_MINIO_ENDPOINT",
    "TASK005_MINIO_ACCESS_KEY",
    "TASK005_MINIO_SECRET_KEY",
    "TASK005_MINIO_BUCKET",
    "TASK005_CLAMAV_HOST",
    "TASK005_RAGFLOW_BASE_URL",
    "TASK005_RAGFLOW_API_KEY",
    "TASK005_RAGFLOW_DATASET_ID"
)

if ($env:TASK005_ALLOW_LIVE_TESTS -ne "1") {
    throw "Set TASK005_ALLOW_LIVE_TESTS=1 only for the dedicated TASK-005 validation stack."
}

$missing = @($required | Where-Object { [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($_)) })
if ($missing.Count -gt 0) {
    throw "Missing TASK-005 validation settings: $($missing -join ', ')"
}

$python = Join-Path $BackendPath ".venv/bin/python"
if ($IsWindows) {
    $python = Join-Path $BackendPath ".venv/Scripts/python.exe"
}
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python -m pytest "$BackendPath/tests/integration/test_task005_live_stack.py" -q
if ($LASTEXITCODE -ne 0) {
    throw "TASK-005 live-stack validation failed with exit code $LASTEXITCODE"
}
