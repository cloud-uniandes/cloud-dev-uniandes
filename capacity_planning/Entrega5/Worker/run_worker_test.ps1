Write-Host "============================================" -ForegroundColor Cyan
Write-Host "PLAN B: Pruebas de Capacidad Worker" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Crear directorios
New-Item -ItemType Directory -Force -Path "reports" | Out-Null

$API_URL = "http://anb-api-alb-556459051.us-east-1.elb.amazonaws.com"

# ===================================================================
# PRUEBA 1: 50 MB - 1 Worker - Saturación
# ===================================================================
Write-Host "`n[1/6] Prueba: 50MB, 1 Worker, Saturación (20 videos, 10 min)" -ForegroundColor Yellow
$env:VIDEO_SIZE_MB = "50"
$env:WORKER_CONCURRENCY = "1"
$env:API_BASE_URL = $API_URL

locust -f plan_b_worker_capacity.py `
    --headless `
    --users 10 `
    --spawn-rate 2 `
    --run-time 10m `
    --html reports/plan_b_50mb_1worker_saturation.html `
    --csv reports/plan_b_50mb_1worker_saturation

Start-Sleep -Seconds 60

# ===================================================================
# PRUEBA 2: 50 MB - 1 Worker - Sostenida
# ===================================================================
Write-Host "`n[2/6] Prueba: 50MB, 1 Worker, Sostenida (10 videos, 10 min)" -ForegroundColor Yellow
locust -f plan_b_worker_capacity.py `
    --headless `
    --users 5 `
    --spawn-rate 1 `
    --run-time 10m `
    --html reports/plan_b_50mb_1worker_sustained.html `
    --csv reports/plan_b_50mb_1worker_sustained

Start-Sleep -Seconds 60

# ===================================================================
# PRUEBA 3: 100 MB - 1 Worker - Saturación
# ===================================================================
Write-Host "`n[3/6] Prueba: 100MB, 1 Worker, Saturación (15 videos, 10 min)" -ForegroundColor Yellow
$env:VIDEO_SIZE_MB = "100"

locust -f plan_b_worker_capacity.py `
    --headless `
    --users 10 `
    --spawn-rate 2 `
    --run-time 10m `
    --html reports/plan_b_100mb_1worker_saturation.html `
    --csv reports/plan_b_100mb_1worker_saturation

Start-Sleep -Seconds 60

# ===================================================================
# PRUEBA 4: 100 MB - 1 Worker - Sostenida
# ===================================================================
Write-Host "`n[4/6] Prueba: 100MB, 1 Worker, Sostenida (5 videos, 10 min)" -ForegroundColor Yellow
locust -f plan_b_worker_capacity.py `
    --headless `
    --users 3 `
    --spawn-rate 1 `
    --run-time 10m `
    --html reports/plan_b_100mb_1worker_sustained.html `
    --csv reports/plan_b_100mb_1worker_sustained

Start-Sleep -Seconds 60

# ===================================================================
# PRUEBA 5: 50 MB - 2 Workers - Saturación (si aplica)
# ===================================================================
Write-Host "`n[5/6] Prueba: 50MB, 2 Workers, Saturación (30 videos, 10 min)" -ForegroundColor Yellow
$env:VIDEO_SIZE_MB = "50"
$env:WORKER_CONCURRENCY = "2"

locust -f plan_b_worker_capacity.py `
    --headless `
    --users 15 `
    --spawn-rate 3 `
    --run-time 10m `
    --html reports/plan_b_50mb_2workers_saturation.html `
    --csv reports/plan_b_50mb_2workers_saturation

Start-Sleep -Seconds 60

# ===================================================================
# PRUEBA 6: 100 MB - 2 Workers - Saturación (si aplica)
# ===================================================================
Write-Host "`n[6/6] Prueba: 100MB, 2 Workers, Saturación (20 videos, 10 min)" -ForegroundColor Yellow
$env:VIDEO_SIZE_MB = "100"

locust -f plan_b_worker_capacity.py `
    --headless `
    --users 10 `
    --spawn-rate 2 `
    --run-time 10m `
    --html reports/plan_b_100mb_2workers_saturation.html `
    --csv reports/plan_b_100mb_2workers_saturation

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "✅ TODAS LAS PRUEBAS WORKER COMPLETADAS" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "`nReportes disponibles en: reports\" -ForegroundColor White