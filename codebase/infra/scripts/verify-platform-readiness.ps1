param(
    [Parameter(Mandatory = $true)][string]$EnvFile,
    [Parameter(Mandatory = $true)][string]$ProjectName,
    [Parameter(Mandatory = $true)][string]$LiveHttpsUrl,
    [Parameter(Mandatory = $true)][string]$RagflowDatasetId,
    [Parameter(Mandatory = $true)][string]$BackupOutputDirectory
)

$ErrorActionPreference = "Stop"

function Wait-HttpsHealth([string]$Url) {
    $deadline = (Get-Date).AddMinutes(2)
    do {
        & curl.exe -k --fail --silent --show-error "$Url/healthz" | Out-Null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "HTTPS health endpoint did not become ready"
}

if ($ProjectName -notmatch '^equipment-task011-live-[a-z0-9]{8,}$') {
    throw "ProjectName must be an isolated equipment-task011-live-<random> project"
}
if ($LiveHttpsUrl -notmatch '^https://') { throw "TASK011_LIVE_HTTPS_URL must use HTTPS" }
$resolvedEnv = (Resolve-Path -LiteralPath $EnvFile).Path
$composeFile = "codebase/infra/docker-compose.yml"
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop Linux engine is unavailable" }

$compose = @("compose", "--profile", "validation", "-p", $ProjectName, "--env-file", $resolvedEnv, "-f", $composeFile)
& docker @compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "TASK-011 live stack failed to start" }

$nginx = (& docker @compose ps -q nginx).Trim()
if (!$nginx) { throw "Nginx container is not running" }
$ports = docker inspect $nginx --format '{{json .HostConfig.PortBindings}}'
if ($ports -notmatch '127.0.0.1') { throw "Nginx is not bound to loopback" }

Wait-HttpsHealth $LiveHttpsUrl

& docker @compose exec -T api python -m app.modules.knowledge.ragflow_probe
if ($LASTEXITCODE -ne 0) { throw "RAGFlow probe failed" }

& docker @compose run --rm validator python -m pytest tests/integration/test_task005_postgres.py -q
if ($LASTEXITCODE -ne 0) { throw "Live PostgreSQL validation failed" }

$liveAgentOutput = & docker @compose run --rm -e "TASK005_RAGFLOW_DATASET_ID=$RagflowDatasetId" validator python -m pytest tests/integration/test_task005_live_stack.py -q -rs
$liveAgentOutput | Write-Output
if ($LASTEXITCODE -ne 0) { throw "Live Agent/RAGFlow validation failed" }
if (($liveAgentOutput -join "`n") -match '\bskipped\b') {
    throw "Live Agent/RAGFlow validation must not skip"
}

$env:TASK011_LIVE_HTTPS_URL = $LiveHttpsUrl
python -m pytest codebase/backend/tests/e2e/test_platform_readiness.py -q
if ($LASTEXITCODE -ne 0) { throw "TASK-011 HTTPS E2E failed" }

& docker @compose restart api
if ($LASTEXITCODE -ne 0) { throw "API restart failed" }
Wait-HttpsHealth $LiveHttpsUrl

$backupDirectory = & powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/scripts/backup.ps1 -EnvFile $resolvedEnv -OutputDirectory $BackupOutputDirectory -ProjectName $ProjectName
if ($LASTEXITCODE -ne 0) { throw "Backup failed" }
$restoreProject = "equipment-task011-restore-" + [guid]::NewGuid().ToString("N").Substring(0, 12)
& powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/scripts/restore-verify.ps1 -EnvFile $resolvedEnv -BackupDirectory $backupDirectory[-1] -ProjectName $restoreProject
if ($LASTEXITCODE -ne 0) { throw "Restore verification failed" }

Write-Output "TASK-011 platform readiness: PASS; project=$ProjectName"
