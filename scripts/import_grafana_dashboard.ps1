# Import Grafana Dashboard
$dashboardPath = "infra\grafana\dashboards\cloud_adapter_dashboard.json"
$grafanaUrl = "http://localhost:3000"
$credentials = "admin:admin"
$base64Creds = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($credentials))

# Read dashboard JSON
$dashboardJson = Get-Content $dashboardPath -Raw | ConvertFrom-Json

# Create the payload
$payload = @{
    dashboard = $dashboardJson.dashboard
    overwrite = $true
} | ConvertTo-Json -Depth 100

# Import dashboard
$headers = @{
    "Authorization" = "Basic $base64Creds"
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri "$grafanaUrl/api/dashboards/db" -Method Post -Headers $headers -Body $payload
    Write-Host "[OK] Dashboard imported successfully!" -ForegroundColor Green
    Write-Host "Dashboard UID: $($response.uid)" -ForegroundColor Cyan
    Write-Host "Dashboard URL: $grafanaUrl$($response.url)" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Failed to import dashboard: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
