param([Parameter(Mandatory = $true)][string]$EnvFile)

$ErrorActionPreference = 'Stop'
$resolvedEnv = (Resolve-Path -LiteralPath $EnvFile).Path
$temporaryDirectory = Split-Path -Parent $resolvedEnv
$temporaryRoot = ([IO.Path]::GetFullPath([IO.Path]::GetTempPath())).TrimEnd('\') + '\'
$resolvedDirectory = ([IO.Path]::GetFullPath($temporaryDirectory)).TrimEnd('\') + '\'
if (!$resolvedDirectory.StartsWith($temporaryRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'TASK-005 temporary environment must be under the system temporary directory'
}

docker compose --env-file $resolvedEnv -p equipment-task-005-validation -f codebase/infra/docker-compose.yml down --volumes --remove-orphans
if ($LASTEXITCODE) { throw 'TASK-005 cleanup failed' }
Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
