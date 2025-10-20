# Metrics Troubleshooting Guide

## Current Status

✅ **Metrics Infrastructure:** 27 cloud metrics + 3 router metrics = 30 total metrics
✅ **Metrics Registration:** All 30 metrics registered at API startup  
✅ **Prometheus Configuration:** Correctly configured to scrape API at `host.docker.internal:8000/metrics`
✅ **Grafana Dashboard:** Created with 13 panels
✅ **Alert Rules:** 17 alert rules + 5 recording rules configured

❌ **Issue:** Cloud metrics (27) not appearing in `/metrics` endpoint - only router metrics (3) exposed

---

## Root Cause

The cloud provider metrics are being registered in Python's default `prometheus_client.REGISTRY`, but when the `/metrics` endpoint generates output, it's not including them. This is likely due to:

1. **Registry isolation** - Metrics created at different times may be in different registry instances
2. **Module import order** - The REGISTRY imported at module level may differ from runtime REGISTRY

---

## Solution Options

### Option 1: Direct API Testing (Recommended)

Since the `/images` endpoint exists but uses local captioning by default, we need to force cloud usage:

```python
# Temporarily modify routing_policy.py to always use cloud:
def should_use_cloud(confidence: float, local_latency_ms: int) -> bool:
    return True  # Force cloud for testing
```

Then make requests:
```powershell
# Generate traffic through API
python scripts/test_api_request.py

# Check metrics
curl http://localhost:8000/metrics | Select-String "cloud_"
```

### Option 2: Use Mock Data in Grafana

For demonstration purposes, import the dashboard and use Prometheus' recording rules or manually create sample data.

### Option 3: Fix Registry Issue

The proper fix is to ensure all metrics use the same registry instance. This requires:

1. Creating metrics with explicit registry parameter
2. Ensuring `/metrics` endpoint uses the correct registry
3. Verifying module import order

---

## Quick Test Commands

```powershell
# 1. Check API health
curl http://localhost:8000/healthz

# 2. Check how many metrics are registered at startup
# Look for: [Startup] Total metrics registered: 30

# 3. Check how many metrics are exposed
$response = curl.exe -s http://localhost:8000/metrics
$metrics = ($response | ConvertFrom-Json)
($metrics -split "`n" | Select-String -Pattern "^# HELP").Count
# Should be 30, currently showing 6

# 4. Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# 5. Query Prometheus directly
curl "http://localhost:9090/api/v1/query?query=cloud_requests_total"
```

---

## What's Working

1. ✅ **Metrics module** - Creates all 27 cloud metrics
2. ✅ **Rate limiter** - Creates 6 metrics  
3. ✅ **Circuit breaker** - Creates 5 metrics
4. ✅ **Mock provider** - Integrates with metrics, rate limiter, circuit breaker
5. ✅ **API startup** - Initializes all components
6. ✅ **Prometheus** - Running and configured correctly
7. ✅ **Grafana** - Running with dashboard ready

---

## What's Not Working

1. ❌ **Metrics export** - Only 6 of 30 metrics appear in `/metrics` endpoint
2. ❌ **Prometheus data** - No cloud metrics in Prometheus (because they're not exported)
3. ❌ **Grafana dashboard** - Empty panels (because no data in Prometheus)

---

## Next Steps

**Immediate:**
1. Fix the registry issue in `/metrics` endpoint
2. Verify all 30 metrics appear at `http://localhost:8000/metrics`
3. Wait 15 seconds for Prometheus to scrape
4. Verify metrics in Prometheus: `http://localhost:9090/graph`
5. Check Grafana dashboard: `http://localhost:3000`

**Alternative:**
1. Use the demo data generator script with proper API integration
2. Or temporarily modify routing to force cloud usage
3. Generate real traffic through `/images` endpoint

---

## Debug Checklist

- [ ] API startup shows "Total metrics registered: 30"
- [ ] `/metrics` endpoint returns 30 unique metric families
- [ ] Prometheus target `host.docker.internal:8000` is UP
- [ ] Prometheus query returns data: `cloud_requests_total`
- [ ] Grafana data source test passes
- [ ] Grafana dashboard shows data

---

## Contact Points

- **API:** http://localhost:8000
- **Metrics:** http://localhost:8000/metrics  
- **API Docs:** http://localhost:8000/docs
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)
- **Jaeger:** http://localhost:16686
