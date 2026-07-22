param(
    [string]$ComposeModule = "codebase/infra/ragflow/scripts/compose-execution.psm1",
    [string]$Harness = "codebase/infra/ragflow/tests/cleanup-failure-harness.ps1",
    [string]$FakeCommand = "codebase/infra/ragflow/tests/fake-compose-failure.cmd",
    [string]$PersistenceScript = "codebase/infra/ragflow/scripts/verify-persistence.ps1"
)

$ErrorActionPreference = "Stop"

function Assert-Contract {
    param([bool]$Condition, [string]$Message)

    if (-not $Condition) {
        throw "TASK-004 cleanup failure test failed: $Message"
    }
}

foreach ($path in @($ComposeModule, $Harness, $FakeCommand, $PersistenceScript)) {
    Assert-Contract (Test-Path -LiteralPath $path -PathType Leaf) "missing failure-test input: $path"
}
$persistenceSource = Get-Content -Raw -LiteralPath $PersistenceScript
Assert-Contract ($persistenceSource.Contains("compose-execution.psm1")) "persistence verifier does not load the checked Compose boundary"
$modulePath = (Resolve-Path -LiteralPath $ComposeModule).Path
$harnessPath = (Resolve-Path -LiteralPath $Harness).Path
$fakeCommandPath = (Resolve-Path -LiteralPath $FakeCommand).Path

foreach ($category in @("mysql", "redis", "minio", "elasticsearch")) {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -File $harnessPath `
        -ComposeModule $modulePath -FakeCommand $fakeCommandPath -Category $category 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    Assert-Contract ($exitCode -ne 0) "$category cleanup failure returned exit code 0"
    Assert-Contract (($output -join "`n") -notmatch "cleanup harness: PASS") "$category cleanup failure emitted PASS"
}

Write-Output "TASK-004 cleanup failure behavior: PASS; categories=4"
