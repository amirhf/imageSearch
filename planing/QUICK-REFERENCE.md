# Quick Reference Card

## 🚀 Start Commands

### Start Infrastructure
```powershell
docker-compose -f infra/docker-compose.yml up -d
```

### Start API (Real Models)
```powershell
$env:USE_MOCK_MODELS="false"
.venv\Scripts\uvicorn apps.api.main:app --host 0.0.0.0 --port 8001
```

### Start API (Mock Models - Fast)
```powershell
$env:USE_MOCK_MODELS="true"
.venv\Scripts\uvicorn apps.api.main:app --host 0.0.0.0 --port 8001
```

### Start API (Auto-detect)
```powershell
.venv\Scripts\uvicorn apps.api.main:app --host 0.0.0.0 --port 8001
```

---

## 🧪 Test Commands

```powershell
# Quick API test
.venv\Scripts\python test_final_port8001.py

# Test real models
.venv\Scripts\python test_api_real_models.py

# Test PyTorch
.venv\Scripts\python test_pytorch_install.py

# Test models directly
.venv\Scripts\python test_real_models.py
```

---

## 📡 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8001 | - |
| **API Docs** | http://localhost:8001/docs | - |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger** | http://localhost:16686 | - |

---

## 🔧 Common Tasks

### Upload Image
```powershell
curl -X POST http://localhost:8001/images -F "file=@test_image.jpg"
```

### Search Images
```powershell
curl "http://localhost:8001/search?q=your+search+query&k=5"
```

### Check Health
```powershell
curl http://localhost:8001/healthz
```

### View Metrics
```powershell
curl http://localhost:8001/metrics
```

---

## 🐛 Troubleshooting

### Kill All Python Processes
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Check Port Usage
```powershell
netstat -ano | findstr :8001
```

### Restart Docker
```powershell
docker-compose -f infra/docker-compose.yml restart
```

### Clear Python Cache
```powershell
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse
```

---

## ⚡ Performance

| Mode | Upload | Search | Quality |
|------|--------|--------|---------|
| **Mock** | ~15ms | ~10ms | Random |
| **Real** | ~8500ms | ~2100ms | AI-powered |

---

## ✅ Current Status

- ✅ All endpoints working
- ✅ Mock models operational
- ✅ Real models operational (BLIP + OpenCLIP)
- ✅ PostgreSQL + pgvector working
- ✅ All infrastructure running
- ✅ 100% tests passing
