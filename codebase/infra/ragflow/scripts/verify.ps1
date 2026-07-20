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
$webPorts = @($expanded.services.ragflow.ports | Where-Object { $_.target -eq 80 })
if ($webPorts.Count -ne 1) {
    throw "RAGFlow Web port contract drift: expected one target 80 mapping"
}
$webPort = $webPorts[0].published
$web = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$webPort/"
if ($web.StatusCode -ne 200) {
    throw "RAGFlow Web endpoint is unhealthy: HTTP $($web.StatusCode)"
}

$apiPorts = @($expanded.services.ragflow.ports | Where-Object { $_.target -eq 9380 })
if ($apiPorts.Count -ne 1) {
    throw "RAGFlow API port contract drift: expected one target 9380 mapping"
}
$apiPort = $apiPorts[0].published
$api = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$apiPort/api/v1/system/version"
if ($api.StatusCode -ne 200) {
    throw "RAGFlow API endpoint is unhealthy: HTTP $($api.StatusCode)"
}
$apiContract = $api.Content | ConvertFrom-Json
if ($apiContract.code -ne 0 -or $apiContract.data -ne "v0.25.6" -or $apiContract.message -ne "success") {
    throw "RAGFlow API version contract drift"
}

$versionJson = & docker @composeArgs exec -T ragflow-elasticsearch sh -lc 'curl -fsS -u "elastic:$ELASTIC_PASSWORD" http://localhost:9200/'
if ($LASTEXITCODE -ne 0) {
    throw "Elasticsearch version request failed"
}
$version = ($versionJson | ConvertFrom-Json).version.number
if ($version -notlike "8.11.*") {
    throw "Unexpected Elasticsearch version: $version"
}

$expectedImageDigests = [ordered]@{
    "infiniflow/ragflow:v0.25.6" = "sha256:74595f13bb09c51b1c151ce85d9e06e42cf4371b0c8aeaef222e67253d7c7543"
    "elasticsearch:8.11.3" = "sha256:58a3a280935d830215802322e9a0373faaacdfd646477aa7e718939c2f29292a"
    "mysql:8.0.39" = "sha256:ccb8f749bb5e59f9f8f03bf7282c7ef27a93a1814a24f0a8a926fb4e19b7fb97"
    "pgsty/minio:RELEASE.2026-03-25T00-00-00Z" = "sha256:a72bf37c235a83a73890d2a46c5b36801fed61c335175e0396070bf84a8bbb98"
    "redis:7.4.2-alpine" = "sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952"
}
foreach ($entry in $expectedImageDigests.GetEnumerator()) {
    $image = $entry.Key
    $expectedDigest = $entry.Value
    $digestJson = docker image inspect --format '{{json .RepoDigests}}' $image
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot inspect fixed image: $image"
    }
    $digests = ($digestJson -join "") | ConvertFrom-Json
    if ($digests.Count -eq 0) {
        throw "Missing RepoDigest for fixed image: $image"
    }
    $actualDigests = @($digests | ForEach-Object { ($_ -split "@", 2)[1] })
    if ($actualDigests -notcontains $expectedDigest) {
        throw "Image digest mismatch for $image; expected=$expectedDigest"
    }
    Write-Output "IMAGE $image digest=$expectedDigest"
}

Write-Output "TASK-004 health: PASS; services=5; elasticsearch=$version; web_status=$($web.StatusCode); api_status=$($api.StatusCode); ragflow=$($apiContract.data)"
