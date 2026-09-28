$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $Root ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    Copy-Item -LiteralPath (Join-Path $Root ".env.example") -Destination $EnvFile
    Write-Host "Created .env from .env.example (simulated provider; no API key required)."
}
Push-Location $Root
try {
    docker compose up --build -d
    docker compose ps
    Write-Host "CivicPulse is starting at http://localhost:8080"
} finally {
    Pop-Location
}

