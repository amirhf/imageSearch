# 2. Python to Go Migration for Search Service

Date: 2025-11-27

## Status

Accepted

## Context

The initial implementation of the Image Search API was built entirely in Python (FastAPI). While Python is excellent for rapid development and integrating with ML libraries (like PyTorch/OpenCLIP), it has limitations in high-concurrency scenarios due to the Global Interpreter Lock (GIL) and higher memory overhead per request compared to compiled languages.

As we scale the search functionality, we anticipate high read traffic that requires low latency and high throughput. The search logic itself (vector similarity + keyword matching) is IO-bound (database) and CPU-bound (ranking/fusion), making it a good candidate for optimization.

## Decision

We decided to extract the **read-only search path** into a separate microservice written in **Go**.

The architecture will be:
- **Python API (FastAPI)**: Handles writes (image upload, embedding generation), authentication, and orchestration. It acts as a gateway for search requests, proxying them to the Go service.
- **Go Search Service**: Handles `POST /search` requests. It connects directly to the PostgreSQL database to execute hybrid search queries using `pgx` and `pgvector`.

## Consequences

### Positive
- **Performance**: Go's goroutines and efficient memory management provide higher throughput and lower tail latency for concurrent search requests.
- **Scalability**: The search service can be scaled independently of the heavy Python/ML stack.
- **Resource Efficiency**: Go binaries are small and consume less memory, allowing for higher density in deployment.

### Negative
- **Complexity**: Introduces a polyglot architecture, requiring knowledge of both Python and Go.
- **Duplication**: Some logic (e.g., database models/schemas) might be duplicated or need synchronization between Python and Go codebases.
- **Operational Overhead**: Requires managing an additional service and Docker container.

## Mitigation
- We use a shared database schema managed by Python (Alembic) as the source of truth.
- We implemented a "Shadow Mode" to verify the Go service's correctness against the Python implementation before full switchover.
