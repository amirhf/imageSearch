# Quick Start Guide

## ✅ All Systems Operational

The Image AI Feature Router is now fully functional with mock implementations.

---

## 🚀 Start the API Server

```powershell
# Kill any existing Python processes
taskkill /F /IM python.exe /T

# Wait a moment for ports to clear
Start-Sleep -Seconds 2

# Start the API server on port 8001
.\.venv\Scripts\uvicorn.exe apps.api.main:app --host 0.0.0.0 --port 8001
```

The server will start and display:
```
[WARN] PyTorch unavailable (...), using mock implementations
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

---

## 🧪 Run Tests

### Option 1: Comprehensive Test
```powershell
.\.venv\Scripts\python.exe test_final_port8001.py
```

Expected output:
```
============================================================
  FINAL COMPREHENSIVE TEST - Port 8001
============================================================

[1/5] Health Check...
  [+] PASS - {'status': 'ok'}

[2/5] Upload Image...
  [+] PASS

[3/5] Retrieve Image...
  [+] PASS

[4/5] Search...
  [+] PASS

[5/5] Prometheus Metrics...
  [+] PASS

[+] ALL TESTS PASSED! System is fully operational.
```

### Option 2: FastAPI TestClient
```powershell
.\.venv\Scripts\python.exe test_with_testclient.py
```

---

## 📡 API Endpoints

### Health Check
```powershell
curl http://localhost:8001/healthz
```

### Upload Image (File)
```powershell
curl -X POST http://localhost:8001/images `
  -F "file=@test_image.jpg"
```

### Upload Image (URL)
```powershell
curl -X POST http://localhost:8001/images `
  -H "Content-Type: application/json" `
  -d '{"url": "https://example.com/image.jpg"}'
```

### Retrieve Image by ID
```powershell
curl http://localhost:8001/images/{image_id}
```

### Search Images
```powershell
curl "http://localhost:8001/search?q=room&k=5"
```

### Prometheus Metrics
```powershell
curl http://localhost:8001/metrics
```

---

## 🐳 Docker Services

Make sure Docker services are running:

```powershell
docker-compose up -d
```

Services:
- **PostgreSQL** (port 5432) - Vector database
- **Qdrant** (port 6333) - Alternative vector store
- **Prometheus** (port 9090) - Metrics collection
- **Grafana** (port 3000) - Metrics visualization
- **Jaeger** (port 16686) - Distributed tracing

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (optional):
```bash
# Vector backend: "pgvector" or "qdrant"
VECTOR_BACKEND=pgvector

# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_router

# Qdrant (if using)
QDRANT_URL=http://localhost:6333

# Force mock models
USE_MOCK_MODELS=auto  # auto | true | false
```

### Using Mock vs Real Models

**Mock Models (Current - No PyTorch):**
- Fast (~15ms per image)
- Deterministic results
- No ML dependencies
- Good for development/testing

**Real Models (Requires PyTorch):**
1. Install VC++ Redistributable
2. Fix PyTorch DLL issues
3. Set `USE_MOCK_MODELS=false`
4. Restart API

---

## 📊 Sample Workflow

```powershell
# 1. Start services
docker-compose up -d
Start-Sleep -Seconds 5

# 2. Start API
.\.venv\Scripts\uvicorn.exe apps.api.main:app --host 0.0.0.0 --port 8001

# In another terminal:

# 3. Upload an image
curl -X POST http://localhost:8001/images -F "file=@test_image.jpg"
# Response: {"id":"abc123","caption":"...","origin":"local","confidence":0.76}

# 4. Search for similar images
curl "http://localhost:8001/search?q=room&k=5"
# Response: {"query":"room","results":[{"id":"abc123","caption":"...","score":0.95}]}

# 5. Check metrics
curl http://localhost:8001/metrics
```

---

## 🎯 What's Working

✅ Image upload (file & URL)  
✅ Auto-captioning (mock)  
✅ Image embedding (mock 512-dim vectors)  
✅ Text embedding (mock 512-dim vectors)  
✅ Vector storage (PostgreSQL + pgvector)  
✅ Vector search (cosine similarity)  
✅ Prometheus metrics  
✅ All API endpoints  

---

## 📝 Notes

- **Port 8001** is used instead of 8000 due to Windows port conflict
- **Mock models** are deterministic and fast
- **pgvector** is configured for 512-dimensional vectors (OpenCLIP ViT-B-32)
- **Database** auto-creates schema on startup

---

## 🆘 Troubleshooting

### Server won't start (port conflict)
```powershell
# Kill all Python processes
taskkill /F /IM python.exe /T

# Wait for TIME_WAIT to clear
Start-Sleep -Seconds 60

# Try again
```

### Database connection error
```powershell
# Restart PostgreSQL
docker-compose restart postgres

# Wait for it to be ready
Start-Sleep -Seconds 10
```

### Tests failing
```powershell
# Clear Python cache
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse

# Restart API
```

---

**Ready to go! 🚀**
