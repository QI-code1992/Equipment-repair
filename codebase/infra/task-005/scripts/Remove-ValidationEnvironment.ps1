param([Parameter(Mandatory = $true)][string]$EnvFile)

$ErrorActionPreference = 'Stop'
$resolvedEnv = (Resolve-Path -LiteralPath $EnvFile).Path
$temporaryDirectory = Split-Path -Parent $resolvedEnv
$temporaryRoot = ([IO.Path]::GetFullPath([IO.Path]::GetTempPath())).TrimEnd('\') + '\'
$resolvedDirectory = ([IO.Path]::GetFullPath($temporaryDirectory)).TrimEnd('\') + '\'
if (!$resolvedDirectory.StartsWith($temporaryRoot, [StringComparison]::OrdinalIgnoreCase) -or
    (Split-Path -Leaf $temporaryDirectory) -notmatch '^equipment-task005-[0-9a-fA-F-]{36}$' -or
    (Split-Path -Leaf $resolvedEnv) -ne 'task005.env') {
    throw 'TASK-005 temporary environment must be under the system temporary directory'
}
$markerFile = Join-Path $temporaryDirectory 'task005-validation-marker'
if (!(Test-Path -LiteralPath $markerFile) -or (Get-Content -Raw -LiteralPath $markerFile) -ne 'TASK005_VALIDATION_ENVIRONMENT') {
    throw 'TASK-005 temporary environment marker is invalid'
}

$cleanupFailure = $null
docker compose --profile validation --env-file $resolvedEnv -p equipment-task-005-validation -f codebase/infra/docker-compose.yml down --volumes --remove-orphans
if ($LASTEXITCODE) { $cleanupFailure = 'TASK-005 cleanup failed' }
Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
if ($cleanupFailure) { throw $cleanupFailure }
