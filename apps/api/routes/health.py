"""Health check and metrics routes"""
from fastapi import APIRouter, Response
import asyncio

router = APIRouter(tags=["health"])


@router.get("/", include_in_schema=False)
def root():
    return {"status": "ok"}


@router.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


@router.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


@router.get("/_ah/health", include_in_schema=False)
def gcp_health():
    # Common GCP health endpoint
    return {"status": "ok"}


async def _generate_metrics_async():
    """Helper to generate metrics in thread pool to avoid blocking"""
    from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST
    
    # Run in thread pool to prevent blocking event loop
    loop = asyncio.get_event_loop()
    metrics_output = await loop.run_in_executor(None, generate_latest, REGISTRY)
    return metrics_output, CONTENT_TYPE_LATEST


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Use timeout to prevent hanging
        metrics_output, content_type = await asyncio.wait_for(
            _generate_metrics_async(), 
            timeout=5.0
        )
        return Response(content=metrics_output, media_type=content_type)
    except asyncio.TimeoutError:
        return Response(content="Metrics generation timed out", status_code=504)
    except Exception as e:
        return Response(content=f"Error generating metrics: {str(e)}", status_code=500)
