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

function Assert-StaticAssetContentTypes([string]$Url) {
    $index = & curl.exe -k --fail --silent --show-error "$Url/"
    if ($LASTEXITCODE -ne 0) { throw "HTTPS frontend entry could not be fetched" }
    $assets = @(
        @{ Pattern = '<script[^>]+src="(?<path>/assets/[^"?]+\.js)"'; ContentType = 'application/javascript' },
        @{ Pattern = '<link[^>]+href="(?<path>/assets/[^"?]+\.css)"'; ContentType = 'text/css' }
    )
    foreach ($asset in $assets) {
        $match = [regex]::Match(($index -join "`n"), $asset.Pattern)
        if (!$match.Success) { throw "Frontend entry does not reference the expected static asset" }
        $headers = & curl.exe -k --fail --silent --show-error -I "$Url$($match.Groups['path'].Value)"
        if ($LASTEXITCODE -ne 0) { throw "Frontend static asset could not be fetched" }
        if (($headers -join "`n") -notmatch "(?im)^Content-Type:\s*$([regex]::Escape($asset.ContentType))(?:;|\s|$)") {
            throw "Frontend static asset must be served as $($asset.ContentType)"
        }
    }
}

function Initialize-MinioBucket([string[]]$Compose, [string]$EnvironmentFile) {
    $values = @{}
    Get-Content -LiteralPath $EnvironmentFile | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object {
        $pair = $_.Split('=', 2)
        $values[$pair[0]] = $pair[1]
    }
    foreach ($name in @("MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "MINIO_BUCKET")) {
        if (!$values[$name]) { throw "$name is required in the environment file" }
    }
    $minio = (& docker @Compose ps -q minio).Trim()
    if (!$minio) { throw "MinIO container is not running" }
    & docker exec $minio mc alias set task011 http://127.0.0.1:9000 $values["MINIO_ACCESS_KEY"] $values["MINIO_SECRET_KEY"] | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "MinIO alias configuration failed" }
    $minioBucket = $values["MINIO_BUCKET"]
    & docker exec $minio mc mb --ignore-existing "task011/$minioBucket" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "MinIO bucket creation failed" }
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

Initialize-MinioBucket $compose $resolvedEnv

$nginx = (& docker @compose ps -q nginx).Trim()
if (!$nginx) { throw "Nginx container is not running" }
$ports = docker inspect $nginx --format '{{json .HostConfig.PortBindings}}'
if ($ports -notmatch '127.0.0.1') { throw "Nginx is not bound to loopback" }

Wait-HttpsHealth $LiveHttpsUrl
Assert-StaticAssetContentTypes $LiveHttpsUrl

& docker @compose exec -T api python -m app.modules.knowledge.ragflow_probe
if ($LASTEXITCODE -ne 0) { throw "RAGFlow probe failed" }

& docker @compose run --rm validator python -m pytest tests/integration/test_task005_postgres.py -q
if ($LASTEXITCODE -ne 0) { throw "Live PostgreSQL validation failed" }

$postgres = (& docker @compose ps -q postgres).Trim()
if (!$postgres) { throw "PostgreSQL container is not running" }
$postgresUser = (& docker exec $postgres printenv POSTGRES_USER).Trim()
$postgresPassword = (& docker exec $postgres printenv POSTGRES_PASSWORD).Trim()
$postgresDatabase = (& docker exec $postgres printenv POSTGRES_DB).Trim()
$task005Database = "equipment_task5_validation_" + [guid]::NewGuid().ToString("N").Substring(0, 12)
$task005Dsn = "postgresql://${postgresUser}:${postgresPassword}@postgres:5432/$task005Database"
$task005Worker = ""

& docker exec $postgres psql -U $postgresUser -d $postgresDatabase -v ON_ERROR_STOP=1 -c "CREATE DATABASE $task005Database" *> $null
if ($LASTEXITCODE -ne 0) { throw "TASK-005 validation database creation failed" }
try {
    & docker @compose run --rm --no-deps -e "POSTGRES_DSN=$task005Dsn" migrate alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "TASK-005 validation database migration failed" }

    $task005Worker = "$ProjectName-task005-worker-" + [guid]::NewGuid().ToString("N").Substring(0, 8)
    & docker @compose run -d --name $task005Worker --no-deps -e "POSTGRES_DSN=$task005Dsn" worker
    if ($LASTEXITCODE -ne 0) { throw "TASK-005 validation worker startup failed" }

    $liveAgentOutput = & docker @compose run --rm --no-deps -e "TASK005_POSTGRES_DSN=$task005Dsn" -e "TASK005_RAGFLOW_DATASET_ID=$RagflowDatasetId" validator python -m pytest tests/integration/test_task005_live_stack.py -q -rs
    $liveAgentOutput | Write-Output
    if ($LASTEXITCODE -ne 0) { throw "Live Agent/RAGFlow validation failed" }
    if (($liveAgentOutput -join "`n") -match '\bskipped\b') {
        throw "Live Agent/RAGFlow validation must not skip"
    }
}
finally {
    if ($task005Worker) { & docker rm -f $task005Worker *> $null }
    & docker exec $postgres psql -U $postgresUser -d $postgresDatabase -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $task005Database WITH (FORCE)" *> $null
}

$containerLiveHttpsUrl = $LiveHttpsUrl -replace '://127\.0\.0\.1(?=[:/]|$)', '://host.docker.internal'
& docker @compose run --rm --no-deps -e "TASK011_LIVE_HTTPS_URL=$containerLiveHttpsUrl" validator python -m pytest tests/e2e/test_platform_readiness.py -q
if ($LASTEXITCODE -ne 0) { throw "TASK-011 HTTPS E2E failed" }

& docker @compose restart api
if ($LASTEXITCODE -ne 0) { throw "API restart failed" }
Wait-HttpsHealth $LiveHttpsUrl

$backupOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/scripts/backup.ps1 -EnvFile $resolvedEnv -OutputDirectory $BackupOutputDirectory -ProjectName $ProjectName
if ($LASTEXITCODE -ne 0) { throw "Backup failed" }
$backupDirectory = ([string](@($backupOutput | Select-Object -Last 1))).Trim()
if (!(Test-Path -LiteralPath $backupDirectory -PathType Container)) { throw "Backup output directory is invalid" }
$restoreProject = "equipment-task011-restore-" + [guid]::NewGuid().ToString("N").Substring(0, 12)
& powershell -NoProfile -ExecutionPolicy Bypass -File codebase/infra/scripts/restore-verify.ps1 -EnvFile $resolvedEnv -BackupDirectory $backupDirectory -ProjectName $restoreProject
if ($LASTEXITCODE -ne 0) { throw "Restore verification failed" }

Write-Output "TASK-011 platform readiness: PASS; project=$ProjectName"
