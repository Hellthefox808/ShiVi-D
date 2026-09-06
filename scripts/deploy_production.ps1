# ==============================================================================
# ShiVi Production Deployment Orchestrator (Windows PowerShell)
# ==============================================================================
param (
    [switch]$BuildOnly = $false,
    [switch]$Enterprise = $false
)

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Green
Write-Host "  🚀 SHIVI - SMART HYBRID INTELLIGENT VIRTUAL INTEGRATION (WINDOWS DEPLOY)      " -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green

# Verify Docker is available
try {
    $dockerVersion = docker --version
    Write-Host "[INFO] Docker detected: $dockerVersion" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Docker CLI not found. Ensure Docker Desktop is installed and in PATH." -ForegroundColor Red
    exit 1
}

# Generate .env.production if missing
$envFile = Join-Path $PSScriptRoot "..\.env.production"
if (-not (Test-Path $envFile)) {
    Write-Host "[WARN] .env.production not found. Generating default production secrets..." -ForegroundColor Yellow
    $secretBytes = New-Object byte[] 32
    (New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($secretBytes)
    $jwtSecret = -join ($secretBytes | ForEach-Object { "{0:x2}" -f $_ })

    $envContent = @"
NODE_ENV=production
ENVIRONMENT=production
JWT_SECRET=$jwtSecret
PORT=8000
FRONTEND_PORT=3000
DATABASE_URL=sqlite+aiosqlite:////data/shivi_production.db
CORS_ORIGINS=*
"@
    Set-Content -Path $envFile -Value $envContent
    Write-Host "[OK] .env.production generated." -ForegroundColor Green
}

$composeFile = Join-Path $PSScriptRoot "..\docker-compose.prod.yml"
$profileArgs = @()
if ($Enterprise) {
    $profileArgs = @("--profile", "enterprise")
}

Write-Host "[1/3] Building production images (FastAPI + Next.js)..." -ForegroundColor Cyan
& docker compose -f $composeFile build @profileArgs

if ($BuildOnly) {
    Write-Host "[SUCCESS] Images built successfully." -ForegroundColor Green
    exit 0
}

Write-Host "[2/3] Starting container cluster..." -ForegroundColor Cyan
& docker compose -f $composeFile up -d @profileArgs

Write-Host "[3/3] Awaiting cluster health readiness (timeout: 60s)..." -ForegroundColor Cyan
$maxRetries = 30
$retryCount = 0
$healthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($backendHealth -and $backendHealth.status -eq "healthy") {
            $healthy = $true
            break
        }
    } catch {
        # continue waiting
    }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 2
    $retryCount++
}

Write-Host ""

if ($healthy) {
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "  ✅ SHIVI PRODUCTION CLUSTER ONLINE & OPERATIONAL" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "  • Unified Web Front:          http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  • Disaster SMS / Satellite:   http://localhost:3000/sms" -ForegroundColor Cyan
    Write-Host "  • Core API REST & Swagger:    http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  • Core Edge Health Probe:     http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Green
} else {
    Write-Host "[WARN] Health probe timed out. Inspecting container logs..." -ForegroundColor Yellow
    & docker compose -f $composeFile logs --tail=30
}
