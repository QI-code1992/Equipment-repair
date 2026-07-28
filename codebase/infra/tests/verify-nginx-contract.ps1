param(
    [string]$EnvFile = "codebase/infra/.env.example",
    [string]$ComposeFile = "codebase/infra/docker-compose.yml"
)

$ErrorActionPreference = "Stop"

$expanded = docker compose --env-file $EnvFile -f $ComposeFile config --format json
if ($LASTEXITCODE -ne 0) { throw "Compose configuration cannot be expanded" }
$config = $expanded | ConvertFrom-Json
$nginx = $config.services.nginx
if ($null -eq $nginx) { throw "Nginx service is required" }
if (@($nginx.ports).Count -ne 1 -or $nginx.ports[0].host_ip -ne "127.0.0.1" -or $nginx.ports[0].target -ne 443) {
    throw "Nginx must be the single loopback HTTPS entry"
}
if ($nginx.networks.PSObject.Properties.Name -notcontains "ingress") {
    throw "Nginx must join the non-internal ingress network"
}

foreach ($name in @("postgres", "redis", "minio", "clamav", "worker", "migrate", "validator")) {
    $service = $config.services.$name
    if ($null -ne $service -and $null -ne $service.ports -and @($service.ports).Count -ne 0) {
        throw "Internal service exposes a host port: $name"
    }
    if ($null -ne $service -and $service.networks.PSObject.Properties.Name -contains "ingress") {
        throw "Internal service must not join ingress: $name"
    }
}

$configPath = Join-Path (Split-Path -Parent $ComposeFile) "nginx/default.conf"
$nginxConfig = Get-Content -Raw -LiteralPath $configPath
foreach ($required in @("listen 443 ssl", "resolver 127.0.0.11", 'set $api_upstream api:8000', 'proxy_pass http://$api_upstream', "proxy_buffering off", "proxy_read_timeout")) {
    if ($nginxConfig -notmatch [regex]::Escape($required)) {
        throw "Nginx contract missing: $required"
    }
}
foreach ($required in @("root /usr/share/nginx/html", 'try_files $uri $uri/ /index.html')) {
    if ($nginxConfig -notmatch [regex]::Escape($required)) {
        throw "Nginx frontend contract missing: $required"
    }
}
if ($nginxConfig -notmatch [regex]::Escape("include /etc/nginx/mime.types")) {
    throw "Nginx frontend contract must load MIME types"
}
if (@($nginx.volumes | Where-Object { $_.target -eq "/usr/share/nginx/html" -and $_.read_only }).Count -ne 1) {
    throw "Nginx must mount the frontend production build"
}

Write-Output "TASK-011 nginx contract: PASS"
