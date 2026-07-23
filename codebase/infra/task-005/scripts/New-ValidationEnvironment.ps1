param([Parameter(Mandatory=$true)][string]$RagflowApiKeyFile)

$ErrorActionPreference = 'Stop'

function New-RandomHex([int]$ByteCount) {
    $bytes = [byte[]]::new($ByteCount)
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return (([BitConverter]::ToString($bytes) -replace '-', '')).ToLowerInvariant()
}

$apiKeyPath = (Resolve-Path -LiteralPath $RagflowApiKeyFile).Path
$gitRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if ($LASTEXITCODE -eq 0 -and $apiKeyPath.StartsWith($gitRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'RAGFlow API key file must be outside the Git worktree'
}
$key = (Get-Content -Raw -LiteralPath $apiKeyPath).Trim()
if (!$key -or $key -match '[\r\n]') { throw 'RAGFlow API key file must contain one non-empty value' }

$dir = Join-Path ([IO.Path]::GetTempPath()) ('equipment-task005-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $dir | Out-Null
$envFile = Join-Path $dir 'task005.env'
$markerFile = Join-Path $dir 'task005-validation-marker'
[IO.File]::WriteAllText($markerFile, 'TASK005_VALIDATION_ENVIRONMENT')
$lines = @(
    'POSTGRES_DB=equipment_task5_validation_live',
    ('POSTGRES_USER=task005_' + (New-RandomHex 6)),
    ('POSTGRES_PASSWORD=' + (New-RandomHex 24)),
    'REDIS_URL=redis://redis:6379/0',
    ('MINIO_ACCESS_KEY=task005' + (New-RandomHex 6)),
    ('MINIO_SECRET_KEY=' + (New-RandomHex 24)),
    ('MINIO_BUCKET=task005-' + (New-RandomHex 6)),
    'RAGFLOW_BASE_URL=http://host.docker.internal:19380',
    "RAGFLOW_API_KEY=$key"
)
[IO.File]::WriteAllLines($envFile, $lines, [Text.UTF8Encoding]::new($false))
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls $envFile /inheritance:r /grant:r "${identity}:(R,W)" *> $null
if ($LASTEXITCODE -ne 0) { throw 'TASK-005 environment file permissions could not be restricted' }
Write-Output ([IO.Path]::GetFullPath($envFile))
