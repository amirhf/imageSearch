# Check current metrics status

Write-Host "`n=== Metrics Status Check ===" -ForegroundColor Cyan

# Count total metrics
$metrics = curl.exe -s http://localhost:8000/metrics
$totalCount = ($metrics | Select-String -Pattern "^# HELP").Count
$createdCount = ($metrics | Select-String -Pattern "_created").Count
$pythonGcCount = ($metrics | Select-String -Pattern "python_gc").Count

Write-Host "`nTotal metric families: $totalCount" -ForegroundColor White
Write-Host "_created metrics: $createdCount" -ForegroundColor $(if ($createdCount -eq 0) { "Green" } else { "Yellow" })
Write-Host "Python GC metrics: $pythonGcCount" -ForegroundColor $(if ($pythonGcCount -eq 0) { "Green" } else { "Yellow" })

# Show cloud metrics
Write-Host "`n=== Cloud Metrics (should be stable) ===" -ForegroundColor Cyan
$metrics | Select-String -Pattern "^cloud_requests_total{" | Select-Object -First 3
$metrics | Select-String -Pattern "^cloud_cost_total" | Select-Object -First 2

# Show rate limiter metrics
Write-Host "`n=== Rate Limiter Metrics ===" -ForegroundColor Cyan
$metrics | Select-String -Pattern "^rate_limiter_requests_allowed" | Select-Object -First 1
$metrics | Select-String -Pattern "^rate_limiter_budget_remaining" | Select-Object -First 1

# Show circuit breaker state
Write-Host "`n=== Circuit Breaker State ===" -ForegroundColor Cyan
$metrics | Select-String -Pattern "^circuit_breaker_state" | Select-Object -First 1

Write-Host "`n"
if ($createdCount -eq 0 -and $pythonGcCount -eq 0) {
    Write-Host "[OK] Metrics are clean - Grafana should be stable now!" -ForegroundColor Green
} else {
    Write-Host "[WARN] Noisy metrics still present - restart API to fix" -ForegroundColor Yellow
}
