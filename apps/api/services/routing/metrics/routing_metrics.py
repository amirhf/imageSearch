from prometheus_client import Counter, Histogram

# Metrics definition
ROUTING_DECISIONS = Counter(
    "router_decisions_total", 
    "Total routing decisions made",
    ["tier", "reason"]
)

ROUTING_LATENCY = Histogram(
    "router_decision_seconds",
    "Time taken to make a routing decision",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1)
)

CACHE_HITS = Counter(
    "router_cache_hits_total",
    "Cache hits by tier",
    ["tier"]  # "edge", "semantic"
)

CACHE_MISSES = Counter(
    "router_cache_misses_total",
    "Cache misses by tier",
    ["tier"]
)
