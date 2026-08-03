function Invoke-ValidationComposeCleanup {
    param([Parameter(Mandatory = $true)][string[]]$ComposeArguments)

    $tracePath = Join-Path ([IO.Path]::GetTempPath()) ("task005-cleanup-$PID.stderr")
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & docker @ComposeArguments down --volumes --remove-orphans 2> $tracePath
    $ErrorActionPreference = $previousErrorAction
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        $details = if (Test-Path -LiteralPath $tracePath) {
            (Get-Content -Raw -LiteralPath $tracePath).Trim()
        } else { '' }
        throw "TASK-005 Compose cleanup failed: $details"
    }
    Remove-Item -LiteralPath $tracePath -Force -ErrorAction SilentlyContinue
}
