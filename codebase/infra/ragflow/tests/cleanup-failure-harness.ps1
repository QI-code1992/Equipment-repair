param(
    [Parameter(Mandatory = $true)]
    [string]$ComposeModule,
    [Parameter(Mandatory = $true)]
    [string]$FakeCommand,
    [Parameter(Mandatory = $true)]
    [ValidateSet("mysql", "redis", "minio", "elasticsearch")]
    [string]$Category
)

$ErrorActionPreference = "Stop"
Import-Module $ComposeModule -Force

$arguments = switch ($Category) {
    "mysql" { @("exec", "ragflow-mysql", "mysql", "-e", "DROP TABLE task004_persistence_probe") }
    "redis" { @("exec", "ragflow-redis", "redis-cli", "DEL", "task004:persistence") }
    "minio" { @("exec", "ragflow-minio", "mc", "rm", "task004/test/object") }
    "elasticsearch" { @("exec", "ragflow-elasticsearch", "curl", "-fsS", "-X", "DELETE", "http://localhost/task004-persistence") }
}

Invoke-CheckedCompose `
    -DockerCommand $FakeCommand `
    -ComposeArguments @() `
    -Arguments $arguments

Write-Output "TASK-004 cleanup harness: PASS"
