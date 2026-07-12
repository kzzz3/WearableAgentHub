# WearableAgent Hub — One-click Start All Services
# Usage: powershell -ExecutionPolicy Bypass -File scripts/start-all.ps1
# Stops all services on Ctrl+C

$ErrorActionPreference = "Continue"
$python = "E:\Miniconda3\envs\expr\python.exe"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WearableAgent Hub — Starting All" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$jobs = @()

function Start-ServiceJob {
    param([string]$Name, [string]$Command, [string]$WorkDir)
    Write-Host "[START] $Name" -ForegroundColor Green
    $proc = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile -Command `"$Command`"" `
        -WorkingDirectory $WorkDir -PassThru -WindowStyle Hidden
    return @{ Name = $Name; Process = $proc }
}

# 1. x402 Payment Service (TypeScript, port 8002)
$jobs += Start-ServiceJob -Name "x402-pay (8002)" `
    -Command "pnpm --filter @wearable-hub/x402-pay dev" `
    -WorkDir $root

Start-Sleep -Seconds 2

# 2. Core Backend (Python/FastAPI, port 8000)
$jobs += Start-ServiceJob -Name "core-backend (8000)" `
    -Command "$python -m uvicorn src.main:app --reload --port 8000" `
    -WorkDir "$root\packages\core"

Start-Sleep -Seconds 2

# 3. Translate Agent (Python, port 8001)
$jobs += Start-ServiceJob -Name "translate-agent (8001)" `
    -Command "$python main.py" `
    -WorkDir "$root\examples\translate-agent"

# 4. Nav Agent (Python, port 8003)
$jobs += Start-ServiceJob -Name "nav-agent (8003)" `
    -Command "$python main.py" `
    -WorkDir "$root\examples\nav-agent"

# 5. Pay Agent (Python, port 8004)
$jobs += Start-ServiceJob -Name "pay-agent (8004)" `
    -Command "$python main.py" `
    -WorkDir "$root\examples\pay-agent"

# 6. Glasses Simulator (Vite, port 5173)
$jobs += Start-ServiceJob -Name "glasses-sim (5173)" `
    -Command "pnpm --filter @wearable-hub/glasses-sim dev" `
    -WorkDir $root

# 7. Watch Simulator (Vite, port 5174)
$jobs += Start-ServiceJob -Name "watch-sim (5174)" `
    -Command "pnpm --filter @wearable-hub/watch-sim dev" `
    -WorkDir $root

# 8. Dashboard (Vite, port 5175)
$jobs += Start-ServiceJob -Name "dashboard (5175)" `
    -Command "pnpm --filter @wearable-hub/dashboard dev" `
    -WorkDir $root

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend:       http://localhost:8000" -ForegroundColor Yellow
Write-Host "  x402 Pay:      http://localhost:8002" -ForegroundColor Yellow
Write-Host "  Translate:     http://localhost:8001" -ForegroundColor Yellow
Write-Host "  Nav Agent:     http://localhost:8003" -ForegroundColor Yellow
Write-Host "  Pay Agent:     http://localhost:8004" -ForegroundColor Yellow
Write-Host "  Glasses HUD:   http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Watch Face:    http://localhost:5174" -ForegroundColor Yellow
Write-Host "  Dashboard:     http://localhost:5175" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Gray

try {
    while ($true) {
        Start-Sleep -Seconds 5
        foreach ($j in $jobs) {
            if ($j.Process.HasExited) {
                Write-Host "[WARN] $($j.Name) exited (code $($j.Process.ExitCode))" -ForegroundColor Red
            }
        }
    }
} finally {
    Write-Host ""
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    foreach ($j in $jobs) {
        if (!$j.Process.HasExited) {
            Stop-Process -Id $j.Process.Id -Force -ErrorAction SilentlyContinue
            Write-Host "[STOP] $($j.Name)" -ForegroundColor Red
        }
    }
    Write-Host "All services stopped." -ForegroundColor Green
}