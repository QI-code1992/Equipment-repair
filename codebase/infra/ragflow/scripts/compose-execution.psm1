function Invoke-CheckedCompose {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DockerCommand,
        [Parameter(Mandatory = $true)]
        [string[]]$ComposeArguments,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & $DockerCommand @ComposeArguments @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    if ($exitCode -ne 0) {
        throw "Docker Compose command failed"
    }
    return $output
}

Export-ModuleMember -Function Invoke-CheckedCompose
