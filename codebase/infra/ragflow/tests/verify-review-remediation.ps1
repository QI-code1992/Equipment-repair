param(
    [string]$VerifyScript = "codebase/infra/ragflow/scripts/verify.ps1",
    [string]$PersistenceScript = "codebase/infra/ragflow/scripts/verify-persistence.ps1"
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
Assert-Contract ($verifySource -match '\.code\s+-ne\s+0') "RAGFlow API response code is not asserted"
Assert-Contract ($verifySource -match '\.data\s+-ne\s+"v0\.25\.6"') "RAGFlow API version contract is not asserted"

Assert-Contract (Test-Path -LiteralPath $PersistenceScript -PathType Leaf) "missing persistence verification script"
$persistenceSource = Get-Content -Raw -LiteralPath $PersistenceScript
Assert-Contract ($persistenceSource -match 'mc\s+alias\s+set') "MinIO S3 client endpoint is not configured"
Assert-Contract ($persistenceSource -match '"mc"\s*,\s*"mb"') "MinIO bucket is not created through the S3 API"
Assert-Contract ($persistenceSource -match '"mc"\s*,\s*"cp"') "MinIO object is not written through the S3 API"
Assert-Contract ($persistenceSource -match '"mc"\s*,\s*"cat"') "MinIO object is not read through the S3 API"
Assert-Contract ($persistenceSource -match 'mc\s+rb') "MinIO probe bucket is not cleaned through the S3 API"
Assert-Contract ($persistenceSource -notmatch '/data/\.task004-persistence-probe') "MinIO persistence still bypasses the S3 API"

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

Write-Output "TASK-004 review remediation contract: PASS"
