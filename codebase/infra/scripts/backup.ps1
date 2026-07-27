param(
    [Parameter(Mandatory = $true)][string]$EnvFile,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$ProjectName
)

$ErrorActionPreference = "Stop"

if ($ProjectName -notmatch '^equipment-task011-[a-z0-9-]+$') {
    throw "ProjectName must be an isolated equipment-task011-* project"
}
$resolvedEnv = (Resolve-Path -LiteralPath $EnvFile).Path
$composeFile = "codebase/infra/docker-compose.yml"
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop Linux engine is unavailable" }

$bucketLine = Get-Content -LiteralPath $resolvedEnv | Where-Object { $_ -match '^MINIO_BUCKET=' } | Select-Object -Last 1
$minioBucket = ($bucketLine -replace '^MINIO_BUCKET=', '').Trim()
if (!$minioBucket) { throw "MINIO_BUCKET is required in the environment file" }

$root = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $root | Out-Null
$backupDirectory = Join-Path $root ("backup-" + (Get-Date -Format "yyyyMMddHHmmss"))
New-Item -ItemType Directory -Path $backupDirectory | Out-Null

$compose = @("compose", "--profile", "validation", "-p", $ProjectName, "--env-file", $resolvedEnv, "-f", $composeFile)
$postgres = (& docker @compose ps -q postgres).Trim()
if (!$postgres) { throw "PostgreSQL container is not running for $ProjectName" }

$containerDump = "/tmp/task011-backup.dump"
& docker exec $postgres sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --file /tmp/task011-backup.dump'
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed" }
try {
    & docker cp "${postgres}:$containerDump" (Join-Path $backupDirectory "postgres.dump") | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Cannot copy PostgreSQL backup from container" }
}
finally {
    & docker exec $postgres rm -f $containerDump *> $null
}

$minio = (& docker @compose ps -q minio).Trim()
if (!$minio) { throw "MinIO container is not running for $ProjectName" }
$minioUser = "$(& docker exec $minio printenv MINIO_ROOT_USER)".Trim()
$minioPassword = "$(& docker exec $minio printenv MINIO_ROOT_PASSWORD)".Trim()
if (!$minioUser -or !$minioPassword) { throw "MinIO credentials are unavailable" }
$minioDirectory = Join-Path $backupDirectory "minio"
$minioArchive = Join-Path $backupDirectory "minio.zip"
& docker exec $minio rm -rf /tmp/task011-minio | Out-Null
& docker exec $minio mkdir -p /tmp/task011-minio | Out-Null
& docker exec $minio mc alias set task011 http://127.0.0.1:9000 $minioUser $minioPassword | Out-Null
& docker exec $minio mc mirror "task011/$minioBucket" /tmp/task011-minio | Out-Null
if ($LASTEXITCODE -ne 0) { throw "MinIO backup mirror failed" }
try {
    & docker cp "${minio}:/tmp/task011-minio" $minioDirectory | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Cannot copy MinIO backup from container" }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory($minioDirectory, $minioArchive)
}
finally {
    Remove-Item -LiteralPath $minioDirectory -Recurse -Force -ErrorAction SilentlyContinue
    & docker exec $minio rm -rf /tmp/task011-minio *> $null
}

$manifest = [ordered]@{
    created_at = (Get-Date).ToUniversalTime().ToString("o")
    project = $ProjectName
    postgres_dump = "postgres.dump"
    minio_archive = "minio.zip"
    postgres_sha256 = (Get-FileHash -Algorithm SHA256 (Join-Path $backupDirectory "postgres.dump")).Hash
    minio_sha256 = (Get-FileHash -Algorithm SHA256 $minioArchive).Hash
}
$manifest | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $backupDirectory "manifest.json")
Write-Output $backupDirectory
