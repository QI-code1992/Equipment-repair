function Invoke-ValidationComposeCleanup {
    param(
        [Parameter(Mandatory = $true)][string[]]$ComposeArguments,
        [string]$TracePath,
        [scriptblock]$TraceCleanup
    )

    if (-not $TracePath) { $TracePath = Join-Path ([IO.Path]::GetTempPath()) ("task005-cleanup-$PID.stderr") }
    $failure = $null
    try {
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & docker @ComposeArguments down --volumes --remove-orphans 2> $TracePath
        $ErrorActionPreference = $previousErrorAction
        if ($LASTEXITCODE -ne 0) {
            $details = if (Test-Path -LiteralPath $TracePath) { (Get-Content -Raw -LiteralPath $TracePath).Trim() } else { '' }
            $failure = [Exception]::new("TASK-005 Compose cleanup failed: $details")
        }
    } catch { $failure = $_.Exception }
    finally {
        try {
            if (Test-Path -LiteralPath $TracePath) {
                if ($TraceCleanup) { & $TraceCleanup $TracePath }
                else { Remove-Item -LiteralPath $TracePath -Force -ErrorAction Stop }
            }
        } catch {
            $cleanupError = $_.Exception.Message
            if ($failure) { $failure = [Exception]::new("$($failure.Message); stderr trace cleanup failed: $cleanupError") }
            else { $failure = [Exception]::new("stderr trace cleanup failed: $cleanupError") }
        }
    }
    if ($failure) { throw $failure }
}
