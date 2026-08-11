$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tools = Join-Path $Root "tools"
$Destination = Join-Path $Tools "cloudflared.exe"
$Url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

New-Item -ItemType Directory -Force -Path $Tools | Out-Null

Write-Host "Baixando cloudflared oficial para Windows 64-bit..."
Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing

Write-Host "Verificando cloudflared..."
& $Destination --version
Write-Host "cloudflared instalado em: $Destination"
