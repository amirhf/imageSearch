from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from prometheus_client import REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR

# Disable automatic _created metrics to reduce noise in Grafana
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = 'True'

# Disable default Python collectors (GC, platform, process) to reduce noise
try:
    REGISTRY.unregister(PROCESS_COLLECTOR)
    REGISTRY.unregister(PLATFORM_COLLECTOR)
    REGISTRY.unregister(GC_COLLECTOR)
except Exception:
    pass  # Already unregistered or not present

# Configure basic logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("imagesearch")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to initialize metrics on startup.
    This ensures all metrics are registered in the same REGISTRY instance.
    """
    # Initialize cloud provider metrics after app is created
    from apps.api.services.cloud_providers.metrics import get_metrics
    from apps.api.services.cloud_providers.rate_limiter import get_rate_limiter
    from apps.api.services.cloud_providers.circuit_breaker import get_circuit_breaker
    from apps.api.services.cloud_providers.factory import CloudProviderFactory
    
    _ = get_metrics()
    _ = get_rate_limiter()
    _ = get_circuit_breaker()
    
    try:
        _ = CloudProviderFactory.create()
    except Exception as e:
        print(f"[WARNING] Could not initialize cloud provider: {e}")
    
    yield


app = FastAPI(title="AI Feature Router", version="0.1.0", lifespan=lifespan)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3100",  # Next.js dev server
        "http://localhost:3000",  # Alternative port
        os.getenv("FRONTEND_URL", "http://localhost:3100")
    ],
    allow_origin_regex=r"https://image-search-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-client-caption", "x-client-confidence"],
    expose_headers=["*"]
)

# ============================================================================
# Route Registration
# ============================================================================
from apps.api.routes import async_jobs, images, search, auth, health

# Health and metrics routes (root level)
app.include_router(health.router)

# Auth routes (/auth/*)
app.include_router(auth.router)
app.include_router(auth.admin_router)

# Image routes (/images/*)
app.include_router(images.router)

# Async job routes (/images/async, /jobs/*)
app.include_router(async_jobs.router)

# Search routes (/search)
app.include_router(search.router)
