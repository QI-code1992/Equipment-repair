param(
    [string]$ProjectName = "equipment-ragflow",
    [string]$InternalNetwork = "equipment-ragflow-internal",
    [string]$AccessNetwork = "equipment-ragflow-access"
)

$ErrorActionPreference = "Stop"

function Get-DockerJson {
    param([string[]]$Arguments)

    $raw = & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed: docker $($Arguments -join ' ')"
    }
    return ($raw -join "") | ConvertFrom-Json
}

$internal = @(Get-DockerJson -Arguments @("network", "inspect", $InternalNetwork))[0]
$access = @(Get-DockerJson -Arguments @("network", "inspect", $AccessNetwork))[0]

if (-not $internal.Internal) {
    throw "Internal dependency network is not marked internal: $InternalNetwork"
}
if ($access.Internal) {
    throw "Access network must not be marked internal: $AccessNetwork"
}

$expectedInternal = @(
    "$ProjectName-ragflow-1",
    "$ProjectName-ragflow-elasticsearch-1",
    "$ProjectName-ragflow-minio-1",
    "$ProjectName-ragflow-mysql-1",
    "$ProjectName-ragflow-redis-1"
) | Sort-Object
$expectedAccess = @("$ProjectName-ragflow-1")
$actualInternal = @($internal.Containers.PSObject.Properties.Value.Name) | Sort-Object
$actualAccess = @($access.Containers.PSObject.Properties.Value.Name) | Sort-Object

if (($actualInternal -join ",") -ne ($expectedInternal -join ",")) {
    throw "Unexpected internal-network membership: $($actualInternal -join ',')"
}
if (($actualAccess -join ",") -ne ($expectedAccess -join ",")) {
    throw "Unexpected access-network membership: $($actualAccess -join ',')"
}

$dependencyServices = @("ragflow-elasticsearch", "ragflow-minio", "ragflow-mysql", "ragflow-redis")
foreach ($service in $dependencyServices) {
    $container = "$ProjectName-$service-1"
    $ports = Get-DockerJson -Arguments @("inspect", $container, "--format", "{{json .NetworkSettings.Ports}}")
    foreach ($port in $ports.PSObject.Properties) {
        if ($null -ne $port.Value) {
            throw "Internal dependency publishes a host port: $container $($port.Name)"
        }
    }
}

$ragflow = Get-DockerJson -Arguments @("inspect", "$ProjectName-ragflow-1")
$ragflowBindings = @($ragflow.NetworkSettings.Ports.PSObject.Properties | Where-Object { $null -ne $_.Value })
if ($ragflowBindings.Count -ne 2) {
    throw "RAGFlow must publish exactly two ports; actual=$($ragflowBindings.Count)"
}
foreach ($binding in $ragflowBindings) {
    $hostBindings = @($binding.Value)
    if ($hostBindings.Count -ne 1 -or $hostBindings[0].HostIp -ne "127.0.0.1") {
        throw "RAGFlow port is not bound exclusively to loopback: $($binding.Name)"
    }
}

$networkNames = @($ragflow.NetworkSettings.Networks.PSObject.Properties.Name) | Sort-Object
if (($networkNames -join ",") -ne ((@($AccessNetwork, $InternalNetwork) | Sort-Object) -join ",")) {
    throw "RAGFlow has unexpected networks: $($networkNames -join ',')"
}

Write-Output "TASK-004 network isolation: PASS; internal_members=5; access_members=1; published_dependencies=0; ragflow_loopback_ports=2"
