param(
    [string]$ComposeFile = "codebase/infra/ragflow/docker-compose.yml",
    [string]$EnvFile = "codebase/infra/.env.local",
    [int]$TimeoutSeconds = 900
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
    throw "Missing local RAGFlow environment file: $EnvFile"
}
$verificationStartedAt = (Get-Date).ToUniversalTime().ToString("o")
$composeArgs = @(
    "compose", "-p", "equipment-ragflow",
    "--env-file", $EnvFile,
    "-f", $ComposeFile
)

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Desktop Linux engine is unavailable"
}

$expectedImages = [ordered]@{
    "ragflow" = @{ image = "infiniflow/ragflow:v0.26.3"; digest = "sha256:8b9a311a86e0f4a38117ca8c354bfe7884e7eafb7ffcea5b3e83a9485ecba28d" }
    "ragflow-elasticsearch" = @{ image = "elasticsearch:8.11.3"; digest = "sha256:58a3a280935d830215802322e9a0373faaacdfd646477aa7e718939c2f29292a" }
    "ragflow-mysql" = @{ image = "mysql:8.0.39"; digest = "sha256:ccb8f749bb5e59f9f8f03bf7282c7ef27a93a1814a24f0a8a926fb4e19b7fb97" }
    "ragflow-minio" = @{ image = "pgsty/minio:RELEASE.2026-03-25T00-00-00Z"; digest = "sha256:a72bf37c235a83a73890d2a46c5b36801fed61c335175e0396070bf84a8bbb98" }
    "ragflow-redis" = @{ image = "redis:7.4.2-alpine"; digest = "sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952" }
}

$expandedJson = & docker @composeArgs config --format json
if ($LASTEXITCODE -ne 0) {
    throw "docker compose config failed during image verification"
}
$expanded = $expandedJson | ConvertFrom-Json
foreach ($entry in $expectedImages.GetEnumerator()) {
    $serviceName = $entry.Key
    $configuredImage = $expanded.services.($serviceName).image
    if ($configuredImage -ne $entry.Value.image) {
        throw "Compose image mismatch for $serviceName; expected=$($entry.Value.image)"
    }
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

$webPorts = @($expanded.services.ragflow.ports | Where-Object { $_.target -eq 80 })
if ($webPorts.Count -ne 1) {
    throw "RAGFlow Web port contract drift: expected one target 80 mapping"
}
$webPort = $webPorts[0].published
$web = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$webPort/"
if ($web.StatusCode -ne 200) {
    throw "RAGFlow Web endpoint is unhealthy: HTTP $($web.StatusCode)"
}

$apiPorts = @($expanded.services.ragflow.ports | Where-Object { $_.target -eq 9380 })
if ($apiPorts.Count -ne 1) {
    throw "RAGFlow API port contract drift: expected one target 9380 mapping"
}
$apiPort = $apiPorts[0].published
$apiDeadline = (Get-Date).AddSeconds(60)
$api = $null
do {
    try {
        $api = Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 "http://127.0.0.1:$apiPort/api/v1/system/version"
    }
    catch {
        $api = $null
    }
    if ($null -ne $api -and $api.StatusCode -eq 200) {
        break
    }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $apiDeadline)
if ($null -eq $api -or $api.StatusCode -ne 200) {
    throw "RAGFlow API endpoint did not become healthy before timeout"
}
$apiContract = $api.Content | ConvertFrom-Json
if ($apiContract.code -ne 0 -or $apiContract.data -ne "v0.26.3" -or $apiContract.message -ne "success") {
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

foreach ($entry in $expectedImages.GetEnumerator()) {
    $serviceName = $entry.Key
    $image = $entry.Value.image
    $expectedDigest = $entry.Value.digest
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

    $containerId = ((& docker @composeArgs ps -q $serviceName) -join "").Trim()
    if ($LASTEXITCODE -ne 0 -or -not $containerId) {
        throw "Cannot resolve running container for $serviceName"
    }
    $runningImageId = ((docker inspect $containerId --format '{{.Image}}') -join "").Trim()
    if ($LASTEXITCODE -ne 0 -or -not $runningImageId) {
        throw "Cannot inspect running image ID for $serviceName"
    }
    $approvedImageId = ((docker image inspect $image --format '{{.Id}}') -join "").Trim()
    if ($LASTEXITCODE -ne 0 -or -not $approvedImageId) {
        throw "Cannot inspect approved image ID for $serviceName"
    }
    if ($runningImageId -ne $approvedImageId) {
        throw "Running container image mismatch for $serviceName"
    }
    Write-Output "IMAGE service=$serviceName tag=$image digest=$expectedDigest runtime_id_match=true"
}

$ragflowLogs = @(& docker @composeArgs logs --since $verificationStartedAt --no-color ragflow 2>&1)
$logsExitCode = $LASTEXITCODE
if ($logsExitCode -ne 0) {
    throw "Cannot inspect RAGFlow logs"
}
$logText = $ragflowLogs -join "`n"
$dependencyFailurePattern = '(?i)(connection refused|failed to connect|cannot connect|authentication failed|access denied|connection timed out|name or service not known|temporary failure in name resolution)'
$dependencyFailureMatches = [regex]::Matches($logText, $dependencyFailurePattern).Count
if ($dependencyFailureMatches -ne 0) {
    throw "RAGFlow dependency connection failure detected; matches=$dependencyFailureMatches"
}

$secretValues = @(
    $expanded.services.ragflow.environment.MYSQL_PASSWORD,
    $expanded.services.ragflow.environment.REDIS_PASSWORD,
    $expanded.services.ragflow.environment.MINIO_PASSWORD,
    $expanded.services.ragflow.environment.ELASTIC_PASSWORD,
    $expanded.services."ragflow-mysql".environment.MYSQL_ROOT_PASSWORD
) | Where-Object { $_ -is [string] -and $_.Length -gt 0 } | Sort-Object -Unique
$secretMatches = 0
foreach ($secret in $secretValues) {
    if ($logText.Contains($secret)) {
        $secretMatches++
    }
}
if ($secretMatches -ne 0) {
    throw "RAGFlow log secret scan failed; matches=$secretMatches"
}

$verificationCompletedAt = (Get-Date).ToUniversalTime().ToString("o")
Write-Output "TASK-004 health: PASS; started_at=$verificationStartedAt; completed_at=$verificationCompletedAt; services=5; elasticsearch=$version; web_status=$($web.StatusCode); api_status=$($api.StatusCode); ragflow=$($apiContract.data); log_summary=lines:$($ragflowLogs.Count),dependency_failures:0,secret_matches:0; exit_codes=docker_info:0,compose_config:0,compose_up:0,compose_ps:0,logs:0"
