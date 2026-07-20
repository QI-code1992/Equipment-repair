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
$services = @("ragflow", "ragflow-mysql", "ragflow-redis", "ragflow-minio", "ragflow-elasticsearch")
$probe = "task004$([guid]::NewGuid().ToString('N'))"
$minioBucket = "task004-$([guid]::NewGuid().ToString('N'))"
$minioObject = "persistence-probe.txt"
$minioTemporaryFile = "/tmp/$minioObject"
$minioAliasCommand = 'mc alias set task004 http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"'

function Invoke-Compose {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & docker @composeArgs @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    if ($exitCode -ne 0) {
        throw "Docker Compose command failed"
    }
    return $output
}

function Get-ContainerEnvironment {
    param([string]$Service)

    $containerId = ((Invoke-Compose -Arguments @("ps", "-q", $Service)) -join "").Trim()
    $raw = & docker inspect $containerId --format "{{json .Config.Env}}"
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot inspect container environment for $Service"
    }
    $environment = @{}
    foreach ($entry in (($raw -join "") | ConvertFrom-Json)) {
        $separator = $entry.IndexOf("=")
        if ($separator -gt 0) {
            $environment[$entry.Substring(0, $separator)] = $entry.Substring($separator + 1)
        }
    }
    return $environment
}

function Wait-AllHealthy {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $rows = @((Invoke-Compose -Arguments @("ps", "--format", "json")) | ConvertFrom-Json)
        $healthy = @($rows | Where-Object { $_.Health -eq "healthy" }).Count
        if ($rows.Count -eq 5 -and $healthy -eq 5) {
            return
        }
        Start-Sleep -Seconds 5
    } while ((Get-Date) -lt $deadline)

    $summary = $rows | Select-Object Service, State, Health | ConvertTo-Json -Compress
    throw "Services did not recover after restart: $summary"
}

function Get-ContainerIds {
    $ids = @{}
    foreach ($service in $services) {
        $ids[$service] = ((Invoke-Compose -Arguments @("ps", "-q", $service)) -join "").Trim()
    }
    return $ids
}

Wait-AllHealthy
$beforeIds = Get-ContainerIds

try {
    $mysqlEnvironment = Get-ContainerEnvironment -Service "ragflow-mysql"
    $redisEnvironment = Get-ContainerEnvironment -Service "ragflow-redis"
    $elasticsearchEnvironment = Get-ContainerEnvironment -Service "ragflow-elasticsearch"

    $mysqlWrite = "CREATE TABLE IF NOT EXISTS task004_persistence_probe (probe_id INT PRIMARY KEY, probe_value VARCHAR(64) NOT NULL); INSERT INTO task004_persistence_probe (probe_id, probe_value) VALUES (1, '$probe') ON DUPLICATE KEY UPDATE probe_value=VALUES(probe_value);"
    Invoke-Compose -Arguments @("exec", "-T", "-e", "MYSQL_PWD=$($mysqlEnvironment.MYSQL_PASSWORD)", "ragflow-mysql", "mysql", "-u$($mysqlEnvironment.MYSQL_USER)", $mysqlEnvironment.MYSQL_DATABASE, "-e", $mysqlWrite) *> $null

    Invoke-Compose -Arguments @("exec", "-T", "-e", "REDISCLI_AUTH=$($redisEnvironment.REDIS_PASSWORD)", "ragflow-redis", "redis-cli", "SET", "task004:persistence", $probe) *> $null

    Invoke-Compose -Arguments @("exec", "-T", "ragflow-minio", "sh", "-lc", $minioAliasCommand) *> $null
    Invoke-Compose -Arguments @("exec", "-T", "ragflow-minio", "mc", "mb", "task004/$minioBucket") *> $null
    Invoke-Compose -Arguments @("exec", "-T", "ragflow-minio", "sh", "-c", "printf '%s' '$probe' > '$minioTemporaryFile'") *> $null
    Invoke-Compose -Arguments @("exec", "-T", "ragflow-minio", "mc", "cp", $minioTemporaryFile, "task004/$minioBucket/$minioObject") *> $null

    $esDocument = "{`"probe`":`"$probe`"}"
    $esDocument | & docker @composeArgs exec -T ragflow-elasticsearch tee /tmp/task004-persistence.json *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot stage Elasticsearch persistence probe"
    }
    Invoke-Compose -Arguments @("exec", "-T", "ragflow-elasticsearch", "curl", "-fsS", "-u", "elastic:$($elasticsearchEnvironment.ELASTIC_PASSWORD)", "-H", "Content-Type: application/json", "-X", "PUT", "http://localhost:9200/task004-persistence/_doc/1", "--data-binary", "@/tmp/task004-persistence.json") *> $null

    Invoke-Compose -Arguments @("restart") *> $null
    Wait-AllHealthy

    $afterIds = Get-ContainerIds
    foreach ($service in $services) {
        if ($beforeIds[$service] -ne $afterIds[$service]) {
            throw "Container was recreated instead of restarted: $service"
        }
    }

    $mysqlRead = "SELECT probe_value FROM task004_persistence_probe WHERE probe_id=1;"
    $mysqlValue = ((Invoke-Compose -Arguments @("exec", "-T", "-e", "MYSQL_PWD=$($mysqlEnvironment.MYSQL_PASSWORD)", "ragflow-mysql", "mysql", "-N", "-s", "-u$($mysqlEnvironment.MYSQL_USER)", $mysqlEnvironment.MYSQL_DATABASE, "-e", $mysqlRead)) -join "").Trim()
    $redisValue = ((Invoke-Compose -Arguments @("exec", "-T", "-e", "REDISCLI_AUTH=$($redisEnvironment.REDIS_PASSWORD)", "ragflow-redis", "redis-cli", "--raw", "GET", "task004:persistence")) -join "").Trim()
    Invoke-Compose -Arguments @("exec", "-T", "ragflow-minio", "sh", "-lc", $minioAliasCommand) *> $null
    $minioValue = ((Invoke-Compose -Arguments @("exec", "-T", "ragflow-minio", "mc", "cat", "task004/$minioBucket/$minioObject")) -join "").Trim()
    $esJson = (Invoke-Compose -Arguments @("exec", "-T", "ragflow-elasticsearch", "curl", "-fsS", "-u", "elastic:$($elasticsearchEnvironment.ELASTIC_PASSWORD)", "http://localhost:9200/task004-persistence/_doc/1")) -join ""
    $esValue = ($esJson | ConvertFrom-Json)._source.probe

    $values = @{
        mysql = $mysqlValue
        redis = $redisValue
        minio = $minioValue
        elasticsearch = $esValue
    }
    foreach ($store in $values.Keys) {
        if ($values[$store] -ne $probe) {
            throw "Persistence mismatch for $store"
        }
    }

    Write-Output "TASK-004 restart persistence: PASS; stores=mysql,redis,minio-s3,elasticsearch; containers_recreated=0"
}
finally {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $mysqlCleanup = "DROP TABLE IF EXISTS task004_persistence_probe;"
    & docker @composeArgs exec -T -e "MYSQL_PWD=$($mysqlEnvironment.MYSQL_PASSWORD)" ragflow-mysql mysql "-u$($mysqlEnvironment.MYSQL_USER)" $mysqlEnvironment.MYSQL_DATABASE -e $mysqlCleanup *> $null
    & docker @composeArgs exec -T -e "REDISCLI_AUTH=$($redisEnvironment.REDIS_PASSWORD)" ragflow-redis redis-cli DEL task004:persistence *> $null
    & docker @composeArgs exec -T ragflow-minio mc rm --force "task004/$minioBucket/$minioObject" *> $null
    & docker @composeArgs exec -T ragflow-minio mc rb --force "task004/$minioBucket" *> $null
    & docker @composeArgs exec -T ragflow-minio mc alias rm task004 *> $null
    & docker @composeArgs exec -T ragflow-minio rm -f $minioTemporaryFile *> $null
    & docker @composeArgs exec -T ragflow-elasticsearch curl -sS -u "elastic:$($elasticsearchEnvironment.ELASTIC_PASSWORD)" -X DELETE http://localhost:9200/task004-persistence *> $null
    & docker @composeArgs exec -T ragflow-elasticsearch rm -f /tmp/task004-persistence.json *> $null
    $ErrorActionPreference = $previousErrorActionPreference
}
