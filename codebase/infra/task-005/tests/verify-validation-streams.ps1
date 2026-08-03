$ErrorActionPreference = 'Stop'

function Assert-Contract([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "TASK-005 validation stream contract failed: $Message" }
}

$script = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot '..\scripts\Invoke-Validation.ps1')
Assert-Contract ($script -match 'cleanupStderr') 'cleanup stderr must be captured'
Assert-Contract ($script -match 'Compose cleanup failed: \$details') 'cleanup failure must include stderr details'
Assert-Contract ($script -match 'Remove-Item -LiteralPath \$cleanupStderr') 'successful cleanup must remove the trace file'
Assert-Contract ($script -match 'if \(\$LASTEXITCODE -ne 0') 'non-zero cleanup exit must remain a failure'

Write-Output 'TASK-005 validation stream contract: PASS'
