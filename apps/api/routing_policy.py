import os

CONF_T = float(os.getenv("CAPTION_CONFIDENCE_THRESHOLD", 0.55))
BUDGET_MS = int(os.getenv("CAPTION_LATENCY_BUDGET_MS", 600))

# TODO: include queue depth + moving p95 latency from metrics

def should_use_cloud(confidence: float, local_latency_ms: int) -> bool:
    return (confidence < CONF_T) or (local_latency_ms > BUDGET_MS)
