# Grafana Dashboards

This directory contains Grafana dashboard configurations for monitoring the Image Search AI Router.

## Dashboards

### Cloud Caption Adapter Dashboard

**File:** `cloud_adapter_dashboard.json`

Comprehensive monitoring dashboard for the cloud caption provider system.

#### Features

- **Overview Stats** - Total requests, success rate, P95 latency, daily cost
- **Request Rate** - Time series of successful and failed requests
- **Cost Tracking** - Daily cost with budget visualization
- **Rate Limiter** - Current requests/minute gauge
- **Circuit Breaker** - State indicator (CLOSED/OPEN/HALF-OPEN)
- **Model Usage** - Pie chart of requests by model
- **Rate Limit Blocks** - Breakdown by reason
- **Latency Percentiles** - P50, P95, P99 by model
- **Token Usage** - Input/output token rates
- **Error Table** - Recent errors with details

#### Variables

- **Provider** - Filter by cloud provider (openrouter, etc.)
- **Model** - Filter by model (can select multiple)

---

## Installation

### 1. Start Grafana

```bash
# Using docker-compose (from project root)
docker-compose up -d grafana

# Or standalone
docker run -d -p 3000:3000 --name grafana grafana/grafana
```

### 2. Access Grafana

Open: http://localhost:3000

Default credentials:
- Username: `admin`
- Password: `admin`

### 3. Add Prometheus Data Source

1. Go to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Configure:
   - **Name:** prometheus
   - **URL:** http://prometheus:9090 (if using docker-compose)
   - **URL:** http://localhost:9090 (if running locally)
5. Click **Save & Test**

### 4. Import Dashboard

#### Method 1: Via UI (Recommended)

1. Go to **Dashboards** → **Import**
2. Click **Upload JSON file**
3. Select `cloud_adapter_dashboard.json`
4. Select **prometheus** as the data source
5. Click **Import**

#### Method 2: Via API

```bash
# Using curl
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @cloud_adapter_dashboard.json
```

#### Method 3: Provisioning (Auto-import)

Create `/etc/grafana/provisioning/dashboards/dashboard.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/dashboards
```

Copy dashboard JSON to `/etc/grafana/dashboards/`

---

## Dashboard Panels

### Overview Row

**Panel 1: Total Requests (24h)**
- Metric: `sum(increase(cloud_requests_total[24h]))`
- Shows total cloud requests in the last 24 hours

**Panel 2: Success Rate**
- Metric: `sum(rate(cloud_requests_total{status="success"}[5m])) / sum(rate(cloud_requests_total[5m]))`
- Green: >99%, Yellow: >95%, Red: <95%

**Panel 3: P95 Latency**
- Metric: `histogram_quantile(0.95, sum(rate(cloud_request_duration_seconds_bucket[5m])) by (le))`
- Green: <2s, Yellow: <5s, Red: >5s

**Panel 4: Daily Cost**
- Metric: `sum(cloud_daily_cost_usd)`
- Green: <$8, Yellow: <$9, Red: >$9

### Time Series

**Request Rate**
- Successful requests by provider/model
- Failed requests by reason

**Daily Cost & Budget**
- Cumulative daily cost
- Remaining budget line

**Latency Percentiles**
- P50, P95, P99 by model
- Helps identify slow models

**Token Usage Rate**
- Input and output tokens per second
- By model

**Rate Limit Blocks**
- Stacked bars showing blocks by reason
- Per-minute, per-day, budget

### Status Indicators

**Rate Limiter Gauge**
- Shows current requests/minute
- Max: 60 (default)
- Yellow: >45, Red: >55

**Circuit Breaker State**
- **CLOSED ✓** (green) - Normal operation
- **HALF-OPEN ⚠** (yellow) - Testing recovery
- **OPEN ✗** (red) - Service unavailable

### Analysis

**Model Usage Pie Chart**
- Distribution of requests by model
- Last 24 hours

**Error Table**
- Recent errors (last 5 minutes)
- Grouped by provider, model, reason
- Useful for debugging

---

## Alerts

Alerts are configured in `prometheus/alert_rules.yml`.

### Critical Alerts

- **BudgetExhausted** - Daily budget used up
- **CircuitBreakerOpen** - Cloud provider unavailable
- **CriticalErrorRate** - >25% failure rate
- **CriticalDailyCost** - >95% of budget

### Warning Alerts

- **HighDailyCost** - >80% of budget
- **HighErrorRate** - >10% failure rate
- **HighLatency** - P95 >5s
- **RateLimitApproaching** - >50/min
- **LowSuccessRate** - <90%

### Info Alerts

- **NoCloudRequests** - No activity for 10 minutes
- **HighCostPerRequest** - >$0.001/request

---

## Useful Queries

### Cost Analysis

```promql
# Total cost by model (24h)
sum(increase(cloud_cost_total_usd[24h])) by (model)

# Cost per request
sum(rate(cloud_cost_total_usd[1h])) / sum(rate(cloud_requests_total{status="success"}[1h]))

# Daily cost trend
sum(cloud_daily_cost_usd)
```

### Performance Analysis

```promql
# P95 latency by model
histogram_quantile(0.95, sum(rate(cloud_request_duration_seconds_bucket[5m])) by (le, model))

# Requests per second
sum(rate(cloud_requests_total[5m]))

# Error rate
sum(rate(cloud_requests_failed_total[5m])) / sum(rate(cloud_requests_total[5m]))
```

### Rate Limiter

```promql
# Current usage
rate_limiter_requests_per_minute
rate_limiter_requests_today

# Budget status
rate_limiter_budget_used_usd
rate_limiter_budget_remaining_usd

# Block rate
rate(rate_limiter_requests_blocked_total[5m])
```

### Circuit Breaker

```promql
# State (0=closed, 1=open, 2=half_open)
circuit_breaker_state

# Times opened
increase(circuit_breaker_opened_total[1h])

# Failure rate
rate(circuit_breaker_failure_total[5m])
```

---

## Customization

### Change Thresholds

Edit panel thresholds in the dashboard JSON:

```json
"thresholds": {
  "mode": "absolute",
  "steps": [
    { "color": "green", "value": null },
    { "color": "yellow", "value": 8 },
    { "color": "red", "value": 9 }
  ]
}
```

### Add New Panels

1. Edit dashboard in Grafana UI
2. Add panel with desired visualization
3. Configure metric query
4. Save dashboard
5. Export JSON via **Settings** → **JSON Model**

### Modify Refresh Rate

Dashboard refreshes every 10 seconds by default.

Change in JSON:
```json
"refresh": "10s"
```

Or in UI: Top-right dropdown

---

## Troubleshooting

### No Data in Panels

**Check Prometheus:**
```bash
# Test Prometheus is reachable
curl http://localhost:9090/api/v1/query?query=up

# Check if metrics are being scraped
curl http://localhost:9090/api/v1/targets
```

**Check API is exposing metrics:**
```bash
curl http://localhost:8000/metrics
```

### Wrong Time Range

- Use time picker (top-right)
- Default: Last 6 hours
- Try: Last 15 minutes for recent data

### Prometheus Data Source Error

- Verify data source URL in Grafana settings
- Check Prometheus is running: `docker ps | grep prometheus`
- Check network connectivity

### Panels Show "N/A"

- Metrics may not exist yet (no requests processed)
- Try generating some test traffic
- Check metric names match in Prometheus

---

## Best Practices

### Dashboard Organization

- Keep overview stats at top
- Group related panels together
- Use consistent time ranges
- Add panel descriptions

### Performance

- Use recording rules for complex queries
- Limit time range for heavy queries
- Use appropriate refresh intervals
- Consider panel-specific queries

### Alerting

- Set up notification channels (email, Slack, PagerDuty)
- Test alerts with simulated conditions
- Document alert response procedures
- Review and adjust thresholds regularly

---

## Integration with Monitoring Stack

### Docker Compose Setup

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./infra/prometheus:/etc/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    volumes:
      - ./infra/grafana:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
  
  api:
    build: .
    ports:
      - "8000:8000"
```

### Kubernetes Setup

Use ConfigMaps for dashboard provisioning:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
data:
  cloud-adapter.json: |
    <dashboard JSON content>
```

---

## Additional Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)

---

## Support

For issues or questions:
1. Check metric names in Prometheus: http://localhost:9090
2. Verify data source configuration in Grafana
3. Review Prometheus logs: `docker logs prometheus`
4. Review Grafana logs: `docker logs grafana`
