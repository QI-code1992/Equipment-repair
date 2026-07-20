param(
    [string]$VerifyScript = "codebase/infra/ragflow/scripts/verify.ps1",
    [string]$IsolationScript = "codebase/infra/ragflow/scripts/verify-isolation.ps1",
    [string]$PersistenceScript = "codebase/infra/ragflow/scripts/verify-persistence.ps1",
    [string]$Runbook = "08-release-handoff/RUNBOOK.md"
)

$ErrorActionPreference = "Stop"

function Assert-Contract {
    param([bool]$Condition, [string]$Message)

    if (-not $Condition) {
        throw "TASK-004 review remediation failed: $Message"
    }
}

Assert-Contract (Test-Path -LiteralPath $VerifyScript -PathType Leaf) "missing runtime verification script"

$verifySource = Get-Content -Raw -LiteralPath $VerifyScript
Assert-Contract ($verifySource -match 'target\s+-eq\s+9380') "RAGFlow API port 9380 is not selected"
Assert-Contract ($verifySource -match '/api/v1/system/version') "RAGFlow API version endpoint is not probed"
Assert-Contract ($verifySource -match '\$apiDeadline') "RAGFlow API probe has no bounded startup retry"
Assert-Contract ($verifySource -match 'Invoke-WebRequest\s+-UseBasicParsing\s+-TimeoutSec\s+\d+\s+"http://127\.0\.0\.1:\$webPort/') "RAGFlow Web probe has no finite request timeout"
Assert-Contract ($verifySource -match '\.code\s+-ne\s+0') "RAGFlow API response code is not asserted"
Assert-Contract ($verifySource -match '\.data\s+-ne\s+"v0\.25\.6"') "RAGFlow API version contract is not asserted"

Assert-Contract (Test-Path -LiteralPath $PersistenceScript -PathType Leaf) "missing persistence verification script"
$persistenceSource = Get-Content -Raw -LiteralPath $PersistenceScript
Assert-Contract ($persistenceSource -match 'mc\s+alias\s+set') "MinIO S3 client endpoint is not configured"
Assert-Contract ($persistenceSource -match '"mc"\s*,\s*"mb"') "MinIO bucket is not created through the S3 API"
Assert-Contract ($persistenceSource -match '"mc"\s*,\s*"cp"') "MinIO object is not written through the S3 API"
Assert-Contract ($persistenceSource -match '"mc"\s*,\s*"cat"') "MinIO object is not read through the S3 API"
Assert-Contract ($persistenceSource -match '"mc"\s*,\s*"rb"') "MinIO probe bucket is not cleaned through the S3 API"
Assert-Contract ($persistenceSource -notmatch '/data/\.task004-persistence-probe') "MinIO persistence still bypasses the S3 API"
Assert-Contract ($persistenceSource -match '\$verificationSucceeded\s*=\s*\$false') "persistence verification has no failure-preservation state"
Assert-Contract ($persistenceSource -match 'if\s*\(\$verificationSucceeded\)\s*\{[\s\S]*DROP TABLE') "persistence probes are not conditionally cleaned only after success"
$finallyIndex = $persistenceSource.IndexOf("finally {")
$passIndex = $persistenceSource.LastIndexOf('Write-Output "TASK-004 restart persistence: PASS')
Assert-Contract ($finallyIndex -ge 0) "persistence verifier has no guarded cleanup block"
Assert-Contract ($passIndex -gt $finallyIndex) "persistence PASS is emitted before cleanup completes"
$finallySource = $persistenceSource.Substring($finallyIndex)
Assert-Contract ($finallySource -notmatch '&\s+docker\s+@composeArgs') "persistence cleanup bypasses checked Compose execution"
Assert-Contract ($finallySource -match '\$mysqlCleanup\s*=\s*"DROP TABLE[\s\S]*Invoke-Compose[\s\S]*\$mysqlCleanup') "MySQL cleanup is not exit-code checked"
Assert-Contract ($finallySource -match 'Invoke-Compose[\s\S]*redis-cli[\s\S]*DEL') "Redis cleanup is not exit-code checked"
Assert-Contract ($finallySource -match 'Invoke-Compose[\s\S]*"mc"\s*,\s*"rm"') "MinIO object cleanup is not exit-code checked"
Assert-Contract ($finallySource -match 'Invoke-Compose[\s\S]*"mc"\s*,\s*"rb"') "MinIO bucket cleanup is not exit-code checked"
Assert-Contract ($finallySource -match 'Invoke-Compose[\s\S]*curl[\s\S]*-fsS[\s\S]*DELETE') "Elasticsearch cleanup is not fail-fast"

$expectedDigests = @(
    "sha256:74595f13bb09c51b1c151ce85d9e06e42cf4371b0c8aeaef222e67253d7c7543",
    "sha256:58a3a280935d830215802322e9a0373faaacdfd646477aa7e718939c2f29292a",
    "sha256:ccb8f749bb5e59f9f8f03bf7282c7ef27a93a1814a24f0a8a926fb4e19b7fb97",
    "sha256:a72bf37c235a83a73890d2a46c5b36801fed61c335175e0396070bf84a8bbb98",
    "sha256:02419de7eddf55aa5bcf49efb74e88fa8d931b4d77c07eff8a6b2144472b6952"
)
foreach ($digest in $expectedDigests) {
    Assert-Contract ($verifySource.Contains($digest)) "missing approved image digest $digest"
}
Assert-Contract ($verifySource -match 'Image digest mismatch') "image digest drift does not fail verification"
Assert-Contract ($verifySource -match 'Compose image mismatch') "expanded Compose image is not bound to the approved tag"
Assert-Contract ($verifySource -match 'Running container image mismatch') "running container image ID is not bound to the approved image"
Assert-Contract ($verifySource -match "docker inspect.*--format '\{\{\.Image\}\}'") "running container immutable image ID is not inspected"
Assert-Contract ($verifySource -match '\$verificationStartedAt') "verification execution time is not recorded"
Assert-Contract ($verifySource -match 'logs.*--no-color.*ragflow') "RAGFlow logs are not inspected"
Assert-Contract ($verifySource -match 'logs.*--since.*\$verificationStartedAt.*ragflow') "RAGFlow log scan is not bounded to the current verification window"
Assert-Contract ($verifySource -match '\$dependencyFailurePattern') "dependency connection failures are not scanned"
Assert-Contract ($verifySource -match '\$secretValues') "runtime secret values are not scanned against logs"
Assert-Contract ($verifySource -match 'log_summary=') "sanitized log summary is not emitted"
Assert-Contract ($verifySource -match 'exit_codes=') "verification command exit codes are not emitted"

Assert-Contract (Test-Path -LiteralPath $Runbook -PathType Leaf) "missing TASK-004 runbook"
Assert-Contract (Test-Path -LiteralPath $IsolationScript -PathType Leaf) "missing isolation verification script"
$runbookSource = Get-Content -Raw -LiteralPath $Runbook
Assert-Contract ($runbookSource -match '\$RagflowEnvFile\s*=') "runbook does not define an explicit local environment file"
$scriptInvocations = @($runbookSource -split "`n" | Where-Object { $_ -match 'scripts/verify.*\.ps1' })
Assert-Contract ($scriptInvocations.Count -eq 3) "runbook must contain exactly three TASK-004 verifier commands"
$runtimeInvocation = @($scriptInvocations | Where-Object { $_ -match 'scripts/verify\.ps1' })
$isolationInvocation = @($scriptInvocations | Where-Object { $_ -match 'scripts/verify-isolation\.ps1' })
$persistenceInvocation = @($scriptInvocations | Where-Object { $_ -match 'scripts/verify-persistence\.ps1' })
Assert-Contract ($runtimeInvocation.Count -eq 1 -and $runtimeInvocation[0] -match '-EnvFile\s+\$RagflowEnvFile') "runtime verifier omits the explicit local environment file"
Assert-Contract ($persistenceInvocation.Count -eq 1 -and $persistenceInvocation[0] -match '-EnvFile\s+\$RagflowEnvFile') "persistence verifier omits the explicit local environment file"
Assert-Contract ($isolationInvocation.Count -eq 1 -and $isolationInvocation[0] -notmatch '-EnvFile') "runbook passes unsupported EnvFile to isolation verifier"
$tokens = $null
$parseErrors = $null
$isolationAst = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path -LiteralPath $IsolationScript), [ref]$tokens, [ref]$parseErrors
)
Assert-Contract ($parseErrors.Count -eq 0) "isolation verifier cannot be parsed"
$isolationParameters = @($isolationAst.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
Assert-Contract ($isolationParameters -notcontains "EnvFile") "isolation verifier exposes an unused EnvFile parameter"
Assert-Contract ($runbookSource -match '--env-file\s+\$RagflowEnvFile.*\sdown') "runbook down command omits the explicit local environment file"

Write-Output "TASK-004 review remediation contract: PASS"
