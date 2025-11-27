# Search API Contract

This document defines the interface between the Python API Gateway and the Go Search Service.

## Overview
- **Protocol**: HTTP/1.1 (REST)
- **Format**: JSON
- **Direction**: Python API (Client) -> Go Search Service (Server)

## Endpoint: `/search`

**Method**: `POST`

### Request Body

```json
{
  "vector": [0.123, -0.456, ...],  // Required: 512-dim float array (OpenCLIP)
  "k": 10,                          // Optional: Number of results (default: 10)
  "user_id": "uuid-string",         // Optional: For multi-tenant filtering
  "scope": "all",                   // Optional: 'all', 'mine', 'public' (default: 'all')
  "text_query": "search term",      // Optional: Original text query for hybrid search
  "hybrid_boost": 0.3               // Optional: Weight for lexical score (default: configured on server)
}
```

### Response Body

```json
{
  "results": [
    {
      "id": "image-id-123",
      "score": 0.85,                // Combined hybrid score
      "vec_score": 0.80,            // Vector similarity score
      "text_score": 0.50,           // Lexical match score
      "caption": "A description of the image",
      "caption_confidence": 0.95,
      "caption_origin": "cloud",
      "owner_user_id": "uuid-string",
      "visibility": "public",
      "created_at": "2023-10-27T10:00:00Z",
      "payload": {}                 // Additional metadata
    }
  ]
}
```

### Error Responses

- **400 Bad Request**: Invalid vector dimension or missing required fields.
- **500 Internal Server Error**: Database connection failure.
