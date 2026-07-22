param(
    [string]$ComposeFile = "codebase/infra/ragflow/docker-compose.yml",
    [string]$EnvFile = "codebase/infra/.env.example"
)

$ErrorActionPreference = "Stop"

function Assert-Contract {
    param([bool]$Condition, [string]$Message)

    if (-not $Condition) {
        throw "TASK-004 contract failed: $Message"
    }
}

Assert-Contract (Test-Path -LiteralPath $ComposeFile -PathType Leaf) "missing Compose file: $ComposeFile"
Assert-Contract (Test-Path -LiteralPath $EnvFile -PathType Leaf) "missing environment template: $EnvFile"

$raw = docker compose --env-file $EnvFile -f $ComposeFile config --format json
if ($LASTEXITCODE -ne 0) {
    throw "TASK-004 contract failed: docker compose config failed"
}
$config = $raw | ConvertFrom-Json

$expectedImages = @{
    "ragflow" = "infiniflow/ragflow:v0.25.6"
    "ragflow-elasticsearch" = "elasticsearch:8.11.3"
    "ragflow-mysql" = "mysql:8.0.39"
    "ragflow-minio" = "pgsty/minio:RELEASE.2026-03-25T00-00-00Z"
    "ragflow-redis" = "redis:7.4.2-alpine"
}

$serviceNames = @($config.services.PSObject.Properties.Name)
Assert-Contract ($serviceNames.Count -eq 5) "service count must be five"
foreach ($entry in $expectedImages.GetEnumerator()) {
    $service = $config.services.($entry.Key)
    Assert-Contract ($null -ne $service) "missing service $($entry.Key)"
    Assert-Contract ($service.image -eq $entry.Value) "unexpected image for $($entry.Key)"
    Assert-Contract ($null -ne $service.healthcheck) "missing healthcheck for $($entry.Key)"
    Assert-Contract ($service.restart -eq "unless-stopped") "missing restart policy for $($entry.Key)"
}

$internalServices = @("ragflow-mysql", "ragflow-redis", "ragflow-minio", "ragflow-elasticsearch")
foreach ($name in $internalServices) {
    $serviceNetworks = @($config.services.$name.networks.PSObject.Properties.Name)
    Assert-Contract ($null -eq $config.services.$name.ports) "$name publishes a host port"
    Assert-Contract ($serviceNetworks -contains "ragflow-internal") "$name missing internal network"
    Assert-Contract (-not ($serviceNetworks -contains "ragflow-access")) "$name joined access network"
}

Assert-Contract ($config.networks."ragflow-internal".internal -eq $true) "dependency network is not internal"
Assert-Contract ($config.networks."ragflow-internal".name -eq "equipment-ragflow-internal") "internal network name drift"
Assert-Contract ($config.networks."ragflow-access".name -eq "equipment-ragflow-access") "access network name drift"

$ragflowNetworks = @($config.services.ragflow.networks.PSObject.Properties.Name)
Assert-Contract ($ragflowNetworks -contains "ragflow-internal") "ragflow missing internal network"
Assert-Contract ($ragflowNetworks -contains "ragflow-access") "ragflow missing access network"

$published = @($config.services.ragflow.ports)
Assert-Contract ($published.Count -eq 2) "ragflow must publish exactly two loopback ports"
foreach ($port in $published) {
    Assert-Contract ($port.host_ip -eq "127.0.0.1") "ragflow port is not loopback-only"
}

$expectedVolumes = @(
    "ragflow_logs",
    "ragflow_mysql_data",
    "ragflow_redis_data",
    "ragflow_minio_data",
    "ragflow_elasticsearch_data"
)
$volumeNames = @($config.volumes.PSObject.Properties.Name)
foreach ($volume in $expectedVolumes) {
    Assert-Contract ($volumeNames -contains $volume) "missing named volume $volume"
}

$rendered = $raw -join "`n"
Assert-Contract ($rendered -notmatch 'platform') "RAGFlow stack references the platform network"
Assert-Contract ($rendered -notmatch 'postgres') "RAGFlow stack references platform PostgreSQL"
Assert-Contract ($rendered -notmatch 'container_name') "fixed container names are forbidden"

Write-Output "TASK-004 compose contract: PASS"
