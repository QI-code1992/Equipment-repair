$ErrorActionPreference = "Stop"

$backup = "codebase/infra/scripts/backup.ps1"
$restore = "codebase/infra/scripts/restore-verify.ps1"
foreach ($path in @($backup, $restore)) {
    if (!(Test-Path -LiteralPath $path)) { throw "Missing TASK-011 script: $path" }
    $content = Get-Content -Raw -LiteralPath $path
    foreach ($required in @("EnvFile", "ProjectName", "equipment-task011-")) {
        if ($content -notmatch [regex]::Escape($required)) { throw "Missing safety contract '$required' in $path" }
    }
    if ($content -match 'down\s+-v|down\s+--volumes') { throw "Destructive volume cleanup is forbidden in $path" }
}

foreach ($required in @("pg_dump", "MINIO_BUCKET", "mc mirror", "minio.zip")) {
    if ((Get-Content -Raw -LiteralPath $backup) -notmatch [regex]::Escape($required)) {
        throw "Backup contract missing: $required"
    }
}
foreach ($required in @("pg_restore", "MINIO_BUCKET", "mc mirror", "minio.zip")) {
    if ((Get-Content -Raw -LiteralPath $restore) -notmatch [regex]::Escape($required)) {
        throw "Restore contract missing: $required"
    }
}
foreach ($required in @("manifest.project", "-eq $ProjectName", "restore project must differ")) {
    if ((Get-Content -Raw -LiteralPath $restore) -notmatch [regex]::Escape($required)) {
        throw "Restore safety contract missing: $required"
    }
}

Write-Output "TASK-011 backup contract: PASS"
