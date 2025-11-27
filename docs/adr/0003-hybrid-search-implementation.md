# 3. Hybrid Search Implementation

Date: 2025-11-27

## Status

Accepted

## Context

Users need to search for images using both semantic meaning (e.g., "a happy dog") and specific keywords (e.g., "text:cat").
- **Vector Search**: Good for semantic understanding but can miss exact keyword matches or specific entities.
- **Keyword Search**: Good for exact matches but fails at understanding context or synonyms.

We need a way to combine these two approaches to provide the best search experience.

## Decision

We decided to implement **Hybrid Search** using PostgreSQL with `pgvector` and built-in Full-Text Search (FTS).

The implementation details are:
1.  **Vector Search**: Use `pgvector`'s `<=>` (cosine distance) operator on the `embed_vector` column (OpenCLIP embeddings).
2.  **Keyword Search**: Use Postgres `tsvector` column (`search_vector`) indexed with GIN, queried using `websearch_to_tsquery` and ranked with `ts_rank_cd`.
3.  **Fusion**: Combine the scores using a linear combination formula:
    ```sql
    final_score = (vec_score * vec_weight) + (text_score * text_weight)
    ```
    where `vec_score` is normalized cosine similarity (0-1) and `text_score` is the FTS rank.

## Consequences

### Positive
- **Simplicity**: Keeps the stack simple by using Postgres for both vector and keyword search, avoiding the need for a separate search engine like Elasticsearch or Solr initially.
- **Flexibility**: Allows tuning weights (`vec_weight`, `text_weight`) per query or globally to adjust the balance between semantic and keyword matching.
- **Cost**: No extra infrastructure cost (just Postgres).

### Negative
- **Performance**: Postgres FTS is not as feature-rich or performant as dedicated search engines for very large datasets.
- **Tuning**: Linear combination requires careful tuning of weights and normalization of scores, which can be tricky as FTS scores are unbounded.

## Alternatives Considered
- **Reciprocal Rank Fusion (RRF)**: Good for combining ranked lists without score normalization issues, but harder to implement efficiently in a single SQL query compared to linear combination. We might switch to RRF if linear combination proves unstable.
