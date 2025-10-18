# ADR 0001 – Routing Policy: Local‑First with Confidence & SLO Overrides

- **Status**: Proposed
- **Date**: 2025‑10‑18

## Context
Local captioning/embeddings are fast and free but can be weaker on edge cases; cloud VLMs provide higher quality at monetary cost. We need predictable costs and low latency while preserving search quality.

## Decision
Use local models by default. Promote to a cloud provider **only when**:
1. Local caption **confidence** < `τ = 0.55`, or
2. Local p95 **latency** exceeds `600 ms` under load and **queue depth** is high, or
3. The request explicitly sets `quality=high`.

Cloud provider is selected by **cost × latency** table (see `costs/providers.yaml`). Per‑minute and daily budget caps prevent cost runaways. Results are cached by `(image_hash, model_version)`.

## Consequences
- Expect 75–90% local hit‑rate; predictable monthly cost
- Slight quality variance on rare/hard images handled by fallback
- Adds minimal policy complexity but strong product value

## Pricing Inputs (example; keep up‑to‑date)
```yaml
openai_gpt4o_mini:
  input_per_million: 0.15
  output_per_million: 0.60
gemini_flash_lite:
  input_per_million: 0.10
  output_per_million: 0.40
anthropic_claude_3_5_sonnet:
  input_per_million: 3.00
  output_per_million: 15.00
```

## Alternatives Considered
- Cloud‑first with local fallback (too costly)
- Manual operator override only (not adaptive)

## Links
- `/docs` (Swagger)
- Grafana dashboard screenshot
- Benchmark notebook results
