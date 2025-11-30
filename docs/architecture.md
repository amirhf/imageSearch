# System Architecture

This document describes the high-level architecture of the AI Image Search application, specifically focusing on the **Hybrid Cloud Deployment** model used to optimize costs while maintaining scalability.

## Hybrid Deployment Architecture

We utilize a hybrid approach combining **Google Cloud Run** (serverless) for stateless services and **Google Compute Engine** (VM) for stateful/background components.

```mermaid
C4Context
    title System Context Diagram (Hybrid Deployment)

    Person(user, "User", "Web Browser")
    
    System_Boundary(gcp, "Google Cloud Platform") {
        
        System_Boundary(cloud_run, "Cloud Run (Serverless)") {
            Container(ui, "Frontend UI", "Next.js", "User Interface")
            Container(api, "API Service", "FastAPI (Python)", "Orchestrates search & upload")
            Container(search_go, "Search Service", "Go", "High-performance vector search")
        }

        System_Boundary(compute_engine, "Compute Engine (VM: e2-small)") {
            Container(redis, "Redis", "Docker Container", "Job Queue & Caching")
            Container(worker, "Ingestion Worker", "Python Worker", "Async image processing (Embedding/Captioning)")
        }
        
        System_Ext(storage, "Cloudflare R2", "Object Storage (S3 Compatible)")
        System_Ext(db, "Neon Postgres", "PostgreSQL + pgvector")
        System_Ext(openrouter, "OpenRouter", "LLM API (Captioning)")
    }

    Rel(user, ui, "Uses", "HTTPS")
    Rel(ui, api, "API Calls", "HTTPS/JSON")
    
    Rel(api, search_go, "Delegates Search", "gRPC/HTTP")
    Rel(api, redis, "Enqueues Jobs", "TCP:6379")
    Rel(api, db, "Reads/Writes Metadata", "SQL")
    Rel(api, storage, "Generates Presigned URLs", "HTTPS")
    
    Rel(worker, redis, "Consumes Jobs", "TCP:6379")
    Rel(worker, storage, "Uploads Images", "HTTPS")
    Rel(worker, db, "Writes Embeddings", "SQL")
    Rel(worker, openrouter, "Generates Captions", "HTTPS")
    
    Rel(search_go, db, "Vector Search", "SQL")
```

## Component Details

### 1. API Service (Cloud Run)
-   **Technology:** Python, FastAPI.
-   **Role:** Main entry point. Handles auth, upload coordination, and search orchestration.
-   **Scaling:** Scales to zero. Autoscales based on request volume.
-   **Configuration:** `USE_REAL_EMBEDDER=true` (CPU-optimized), `USE_REAL_CAPTIONER=false` (Delegates to Cloud/Mock).

### 2. Search Service (Cloud Run)
-   **Technology:** Go.
-   **Role:** Dedicated microservice for low-latency vector search.
-   **Scaling:** Scales to zero.

### 3. Ingestion Worker (Compute Engine)
-   **Technology:** Python.
-   **Role:** Background processing.
    -   Downloads images.
    -   Generates embeddings (using local Torch/OpenCLIP).
    -   Generates captions (using OpenRouter or Mock).
    -   Stores results in Postgres (pgvector).
-   **Infrastructure:** Runs as a Docker container on a single `e2-small` VM to save costs (vs. always-on Cloud Run).

### 4. Redis (Compute Engine)
-   **Technology:** Redis 7.
-   **Role:** Message broker for Celery/Task queue.
-   **Infrastructure:** Docker container on the same VM as the worker. Exposed via public IP (password protected) to allow Cloud Run access without expensive VPC Connectors.

### 5. Storage & Database
-   **Cloudflare R2:** Cheap, S3-compatible object storage for raw images.
-   **Neon Postgres:** Serverless PostgreSQL with `pgvector` extension for vector similarity search.
