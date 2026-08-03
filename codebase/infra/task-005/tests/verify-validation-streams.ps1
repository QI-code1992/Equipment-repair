$ErrorActionPreference = 'Stop'

function Assert-Contract([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "TASK-005 validation stream contract failed: $Message" }
}

. (Join-Path $PSScriptRoot '..\scripts\Invoke-ValidationComposeCleanup.ps1')
. (Join-Path $PSScriptRoot '..\scripts\Invoke-ValidationCleanup.ps1')
$fakeBin = Join-Path ([IO.Path]::GetTempPath()) ("task005-fake-docker-$PID")
New-Item -ItemType Directory -Path $fakeBin | Out-Null
$fakeDocker = Join-Path $fakeBin 'docker.cmd'
Set-Content -LiteralPath $fakeDocker -Encoding ASCII -Value @(
    '@echo off'
    'echo fake compose stderr 1>&2'
    'exit /b %TASK005_FAKE_DOCKER_EXIT%'
)
$oldPath = $env:PATH
try {
    $env:PATH = "$fakeBin;$oldPath"
    $env:TASK005_FAKE_DOCKER_EXIT = '0'
    Invoke-ValidationComposeCleanup -ComposeArguments @('compose', '-p', 'task005-contract')

    $env:TASK005_FAKE_DOCKER_EXIT = '7'
    try {
        Invoke-ValidationComposeCleanup -ComposeArguments @('compose', '-p', 'task005-contract')
        throw 'expected non-zero cleanup to fail'
    } catch {
        Assert-Contract ($_.Exception.Message -match 'fake compose stderr') 'stderr must remain traceable'
        Assert-Contract ($_.Exception.Message -match 'Compose cleanup failed') 'failure must identify cleanup'
    }
} finally {
    $env:PATH = $oldPath
    Remove-Item -LiteralPath $fakeBin -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Output 'TASK-005 validation stream contract: PASS'

$composeCalls = 0
Invoke-ValidationCleanup -DatasetId '' -DeleteDataset { throw 'must not run' } -ComposeCleanup { $script:composeCalls++ }
Assert-Contract ($composeCalls -eq 1) 'empty dataset id must still run Compose cleanup'
$composeCalls = 0
try {
    Invoke-ValidationCleanup -DatasetId 'dataset-1' -DeleteDataset { throw 'dataset sentinel' } -ComposeCleanup { $script:composeCalls++ ; throw 'compose sentinel' }
    throw 'expected combined cleanup failure'
} catch {
    Assert-Contract ($_.Exception.Message -match 'dataset sentinel') 'dataset failure must be retained'
    Assert-Contract ($_.Exception.Message -match 'compose sentinel') 'Compose failure must be retained'
    Assert-Contract ($composeCalls -eq 1) 'Compose cleanup must run after dataset failure'
}
