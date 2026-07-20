param(
    [string]$ComposeFile = "codebase/infra/ragflow/docker-compose.yml",
    [string]$EnvFile = "codebase/infra/.env.example",
    [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = "Stop"
$composeArgs = @(
    "compose", "-p", "equipment-ragflow",
    "--env-file", $EnvFile,
    "-f", $ComposeFile
)

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Desktop Linux engine is unavailable"
}

& docker @composeArgs up -d
if ($LASTEXITCODE -ne 0) {
    throw "RAGFlow compose up failed"
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$rows = @()
do {
    $psJson = & docker @composeArgs ps --format json
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose ps failed"
    }
    $rows = @($psJson | ConvertFrom-Json)
    $healthy = @($rows | Where-Object { $_.Health -eq "healthy" }).Count
    if ($rows.Count -eq 5 -and $healthy -eq 5) {
        break
    }
    Start-Sleep -Seconds 5
} while ((Get-Date) -lt $deadline)

if ($rows.Count -ne 5 -or $healthy -ne 5) {
    $summary = $rows | Select-Object Service, State, Health | ConvertTo-Json -Compress
    throw "Not all five TASK-004 services became healthy: $summary"
}

$expandedJson = & docker @composeArgs config --format json
if ($LASTEXITCODE -ne 0) {
    throw "docker compose config failed during endpoint verification"
}
$expanded = $expandedJson | ConvertFrom-Json
$webPort = @($expanded.services.ragflow.ports | Where-Object { $_.target -eq 80 })[0].published
$web = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$webPort/"
if ($web.StatusCode -ne 200) {
    throw "RAGFlow Web endpoint is unhealthy: HTTP $($web.StatusCode)"
}

$versionJson = & docker @composeArgs exec -T ragflow-elasticsearch sh -lc 'curl -fsS -u "elastic:$ELASTIC_PASSWORD" http://localhost:9200/'
if ($LASTEXITCODE -ne 0) {
    throw "Elasticsearch version request failed"
}
$version = ($versionJson | ConvertFrom-Json).version.number
if ($version -notlike "8.11.*") {
    throw "Unexpected Elasticsearch version: $version"
}

$images = @(
    "infiniflow/ragflow:v0.25.6",
    "elasticsearch:8.11.3",
    "mysql:8.0.39",
    "pgsty/minio:RELEASE.2026-03-25T00-00-00Z",
    "redis:7.4.2-alpine"
)
foreach ($image in $images) {
    $digestJson = docker image inspect --format '{{json .RepoDigests}}' $image
    $digests = ($digestJson -join "") | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $digests.Count -eq 0) {
        throw "Missing RepoDigest for fixed image: $image"
    }
    Write-Output "IMAGE $image $($digests -join ',')"
}

Write-Output "TASK-004 health: PASS; services=5; elasticsearch=$version; web_status=$($web.StatusCode)"
