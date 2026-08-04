function Invoke-ValidationCleanup {
    param(
        [Parameter(Mandatory = $false)][AllowEmptyString()][string]$DatasetId,
        [Parameter(Mandatory = $true)][scriptblock]$DeleteDataset,
        [Parameter(Mandatory = $true)][scriptblock]$ComposeCleanup
    )

    $failures = [System.Collections.Generic.List[string]]::new()
    if ($DatasetId) {
        try { & $DeleteDataset $DatasetId }
        catch { $failures.Add("dataset cleanup failed: $($_.Exception.Message)") }
    }
    try { & $ComposeCleanup }
    catch { $failures.Add("Compose cleanup failed: $($_.Exception.Message)") }
    if ($failures.Count -gt 0) { throw ($failures -join '; ') }
}

function Throw-ValidationOutcome {
    param([object]$ValidationFailure, [object]$CleanupFailure)
    if ($ValidationFailure -and $CleanupFailure) {
        $validationMessage = if ($ValidationFailure.Exception) { $ValidationFailure.Exception.Message } else { $ValidationFailure.Message }
        $cleanupMessage = if ($CleanupFailure.Exception) { $CleanupFailure.Exception.Message } else { $CleanupFailure.Message }
        throw [Exception]::new("validation failed: $validationMessage; cleanup failed: $cleanupMessage")
    }
    if ($ValidationFailure) { throw $ValidationFailure }
    if ($CleanupFailure) { throw $CleanupFailure }
}
