[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$EnvFile)

$ErrorActionPreference = 'Stop'
$project = 'equipment-task-005-validation'
$composeFile = 'codebase/infra/docker-compose.yml'
. (Join-Path $PSScriptRoot 'Invoke-ValidationComposeCleanup.ps1')

function Read-EnvironmentFile([string]$Path) {
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { $values[$Matches[1]] = $Matches[2] }
    }
    return $values
}

function Assert-ExitCode([string]$Message) {
    if ($LASTEXITCODE -ne 0) { throw $Message }
}

function Convert-ToHostUrl([string]$Url) {
    return $Url.Replace('host.docker.internal', '127.0.0.1')
}

$resolvedEnv = (Resolve-Path -LiteralPath $EnvFile).Path
$settings = Read-EnvironmentFile $resolvedEnv
$required = @('POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'MINIO_BUCKET', 'RAGFLOW_BASE_URL', 'RAGFLOW_API_KEY', 'RAGFLOW_TIMEOUT_SECONDS')
$missing = @($required | Where-Object { -not $settings.ContainsKey($_) -or -not $settings[$_] })
if ($missing.Count -gt 0) { throw "TASK-005 environment is missing required variables: $($missing -join ', ')" }

$compose = @('compose', '--profile', 'validation', '--env-file', $resolvedEnv, '-p', $project, '-f', $composeFile)
$hostRagflowUrl = Convert-ToHostUrl $settings.RAGFLOW_BASE_URL
$headers = @{ Authorization = "Bearer $($settings.RAGFLOW_API_KEY)" }
$datasetId = $null
$validationFailure = $null
try {
    docker @compose config --quiet
    Assert-ExitCode 'TASK-005 Compose configuration is invalid'
    docker @compose up -d --build
    Assert-ExitCode 'TASK-005 validation stack startup failed'

    $ready = $false
    foreach ($attempt in 1..90) {
        $rows = @(docker @compose ps --all --format json | ConvertFrom-Json)
        if ($LASTEXITCODE -eq 0) {
            $byService = @{}
            foreach ($row in $rows) { $byService[$row.Service] = $row }
            $healthy = @('postgres', 'redis', 'minio', 'clamav') | Where-Object { !$byService.ContainsKey($_) -or $byService[$_].Health -ne 'healthy' }
            $migrated = $byService.ContainsKey('migrate') -and $byService['migrate'].ExitCode -eq 0
            if ($healthy.Count -eq 0 -and $migrated) { $ready = $true; break }
        }
        Start-Sleep -Seconds 2
    }
    if (!$ready) { throw 'TASK-005 validation stack did not become ready' }

    $apiRagflowConnected = $false
    foreach ($attempt in 1..30) {
        docker @compose exec -T api python -m app.modules.knowledge.ragflow_probe
        if ($LASTEXITCODE -eq 0) { $apiRagflowConnected = $true; break }
        Start-Sleep -Seconds 2
    }
    if (!$apiRagflowConnected) { throw 'TASK-005 API container cannot resolve or connect to RAGFlow' }

    docker @compose run --rm --no-deps worker python -c "import os; from minio import Minio; c=Minio(os.environ['MINIO_ENDPOINT'], access_key=os.environ['MINIO_ACCESS_KEY'], secret_key=os.environ['MINIO_SECRET_KEY'], secure=False); b=os.environ['MINIO_BUCKET']; c.make_bucket(b) if not c.bucket_exists(b) else None"
    Assert-ExitCode 'TASK-005 MinIO bucket initialization failed'

    $datasetName = 'TASK-005-validation-' + [guid]::NewGuid()
    $dataset = Invoke-RestMethod -Method Post -Uri "$hostRagflowUrl/api/v1/datasets" -Headers $headers -ContentType 'application/json' -Body (@{ name = $datasetName } | ConvertTo-Json -Compress)
    if ($dataset.code -ne 0 -or !$dataset.data.id) { throw 'RAGFlow dataset creation failed' }
    $datasetId = [string]$dataset.data.id

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $validationOutput = @(docker @compose --profile validation run --rm --no-deps --build -e "TASK005_RAGFLOW_DATASET_ID=$datasetId" validator 2>&1)
    $ErrorActionPreference = $previousErrorAction
    $validationOutput | Write-Output
    Assert-ExitCode 'TASK-005 live-stack validation failed'
    if ($validationOutput -match '\bskipped\b') { throw 'TASK-005 live-stack validation was skipped' }
}
catch {
    $validationFailure = $_
}
finally {
    $cleanupFailure = $null
    if ($datasetId) {
        try {
            $deleted = Invoke-RestMethod -Method Delete -Uri "$hostRagflowUrl/api/v1/datasets" -Headers $headers -ContentType 'application/json' -Body (@{ ids = @($datasetId) } | ConvertTo-Json -Compress)
            if ($deleted.code -ne 0) { throw 'RAGFlow dataset cleanup failed' }
        }
        catch { $cleanupFailure = $_ }
    }
    if (!$cleanupFailure) {
        try { Invoke-ValidationComposeCleanup -ComposeArguments $compose }
        catch { $cleanupFailure = $_ }
    }
    if ($validationFailure) { throw $validationFailure }
    if ($cleanupFailure) { throw $cleanupFailure }
}

Write-Output 'TASK-005 live validation: PASS'
