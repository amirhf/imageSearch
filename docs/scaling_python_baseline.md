# Scaling Baseline: Python Search Service

## Environment
- **Date**: 2025-11-27
- **Hardware**: Local Development Environment (Mac)
- **Database**: Postgres + pgvector (Docker)
- **API**: FastAPI (Python 3.11) running locally
- **Models**: OpenCLIP ViT-B-32 (Real inference)

## Benchmark Results

### Latency (Single Client)
| Scenario | Avg Latency | P95 Latency | P99 Latency |
|----------|-------------|-------------|-------------|
| Public Vector Search | 26.23 ms | 33.11 ms | 46.94 ms |
| Auth Hybrid Search (Scope=All) | 28.15 ms | 34.94 ms | 38.78 ms |
| Auth Hybrid Search (Scope=Mine) | 26.39 ms | 31.80 ms | 55.41 ms |

### Throughput (Single Client)
- **~35-40 Requests Per Second (RPS)**
- Note: This is limited by the sequential nature of the benchmark client and local network stack. Concurrent load testing would likely show higher throughput before saturation.

## Analysis
1.  **Hybrid Overhead**: Adding lexical search (`ts_rank_cd`) adds minimal overhead (~2ms) compared to pure vector search.
2.  **Auth Overhead**: Authentication (JWT validation + DB profile check) adds negligible latency (<2ms).
3.  **Bottlenecks**:
    -   **Python GIL**: Not a factor at this load, but will limit concurrency in a single process.
    -   **Database**: Postgres is performing well with the GIN index and HNSW index.
    -   **Network**: Localhost loopback is fast.

## Recommendations for Scaling
1.  **Read Replicas**: Offload search queries to Postgres read replicas.
2.  **Go Migration**: Moving the search path to Go (Phase 4) should improve throughput and reduce P99 latency by avoiding Python overhead and GIL.
3.  **Caching**: Implement Redis caching for frequent queries.
