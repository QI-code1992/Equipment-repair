param(
    [Parameter(Mandatory = $true)][string]$EnvFile,
    [Parameter(Mandatory = $true)][string]$BackupDirectory,
    [Parameter(Mandatory = $true)][string]$ProjectName
)

$ErrorActionPreference = "Stop"

if ($ProjectName -notmatch '^equipment-task011-[a-z0-9-]+$') {
    throw "ProjectName must be an isolated equipment-task011-* project"
}
$resolvedEnv = (Resolve-Path -LiteralPath $EnvFile).Path
$resolvedBackup = (Resolve-Path -LiteralPath $BackupDirectory).Path
$bucketLine = Get-Content -LiteralPath $resolvedEnv | Where-Object { $_ -match '^MINIO_BUCKET=' } | Select-Object -Last 1
$minioBucket = ($bucketLine -replace '^MINIO_BUCKET=', '').Trim()
if (!$minioBucket) { throw "MINIO_BUCKET is required in the environment file" }
$dumpPath = Join-Path $resolvedBackup "postgres.dump"
$minioArchive = Join-Path $resolvedBackup "minio.zip"
if (!(Test-Path -LiteralPath $dumpPath)) { throw "Backup does not contain postgres.dump" }
if (!(Test-Path -LiteralPath $minioArchive)) { throw "Backup does not contain minio.zip" }
$manifest = Get-Content -Raw -LiteralPath (Join-Path $resolvedBackup "manifest.json") | ConvertFrom-Json
if ($manifest.postgres_sha256 -ne (Get-FileHash -Algorithm SHA256 $dumpPath).Hash) { throw "PostgreSQL backup checksum mismatch" }
if ($manifest.minio_sha256 -ne (Get-FileHash -Algorithm SHA256 $minioArchive).Hash) { throw "MinIO backup checksum mismatch" }

$composeFile = "codebase/infra/docker-compose.yml"
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop Linux engine is unavailable" }
$compose = @("compose", "-p", $ProjectName, "--env-file", $resolvedEnv, "-f", $composeFile)
& docker @compose up -d postgres redis minio
if ($LASTEXITCODE -ne 0) { throw "Restore environment failed to start" }

$postgres = ""
$deadline = (Get-Date).AddMinutes(2)
do {
    $postgres = [string](& docker @compose ps -q postgres)
    $postgres = $postgres.Trim()
    if ($postgres) {
        & docker exec $postgres sh -lc 'pg_isready -U "$POSTGRES_USER"' *> $null
        if ($LASTEXITCODE -eq 0) { break }
    }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)
if (!$postgres -or $LASTEXITCODE -ne 0) { throw "PostgreSQL did not become ready for restore" }

$postgresUser = "$(& docker exec $postgres printenv POSTGRES_USER)".Trim()
$postgresDatabase = "$(& docker exec $postgres printenv POSTGRES_DB)".Trim()
if (!$postgresUser -or !$postgresDatabase) { throw "Restore PostgreSQL credentials are unavailable" }

& docker cp $dumpPath "${postgres}:/tmp/task011-restore.dump"
if ($LASTEXITCODE -ne 0) { throw "Cannot copy PostgreSQL backup into restore container" }
try {
    & docker exec $postgres pg_restore -U $postgresUser -d $postgresDatabase --clean --if-exists /tmp/task011-restore.dump
    if ($LASTEXITCODE -ne 0) { throw "pg_restore failed" }
    $result = & docker exec $postgres psql -U $postgresUser -d $postgresDatabase -tAc "SELECT 1"
    if ($LASTEXITCODE -ne 0) { throw "Restored database probe command failed" }
    $result = "$result".Trim()
    if ($result -ne "1") { throw "Restored database probe failed" }
}
finally {
    & docker exec $postgres rm -f /tmp/task011-restore.dump *> $null
}

$minio = [string](& docker @compose ps -q minio)
$minio = $minio.Trim()
if (!$minio) { throw "MinIO did not start for restore" }
$minioUser = "$(& docker exec $minio printenv MINIO_ROOT_USER)".Trim()
$minioPassword = "$(& docker exec $minio printenv MINIO_ROOT_PASSWORD)".Trim()
if (!$minioUser -or !$minioPassword) { throw "MinIO credentials are unavailable" }
$staging = Join-Path ([IO.Path]::GetTempPath()) ("equipment-task011-minio-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $staging | Out-Null
try {
    Expand-Archive -LiteralPath $minioArchive -DestinationPath $staging
    & docker cp $staging "${minio}:/tmp/task011-minio"
    if ($LASTEXITCODE -ne 0) { throw "Cannot copy MinIO backup into restore container" }
    & docker exec $minio mc alias set task011 http://127.0.0.1:9000 $minioUser $minioPassword
    if ($LASTEXITCODE -ne 0) { throw "MinIO alias configuration failed" }
    & docker exec $minio mc mb --ignore-existing "task011/$minioBucket"
    if ($LASTEXITCODE -ne 0) { throw "MinIO bucket creation failed" }
    & docker exec $minio mc mirror --overwrite /tmp/task011-minio "task011/$minioBucket"
    if ($LASTEXITCODE -ne 0) { throw "MinIO restore mirror failed" }
}
finally {
    Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
    & docker exec $minio rm -rf /tmp/task011-minio *> $null
}

Write-Output "TASK-011 restore verification: PASS; project=$ProjectName"
