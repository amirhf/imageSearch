import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

COLL = "images"

class QdrantStore:
    def __init__(self):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=url)
        try:
            self.client.get_collection(COLL)
        except Exception:
            self.client.recreate_collection(
                collection_name=COLL,
                vectors_config=qm.VectorParams(size=512, distance=qm.Distance.COSINE),  # Match OpenCLIP ViT-B-32
            )

    async def upsert_image(self, image_id: str, caption: str, caption_confidence: float, caption_origin: str, img_vec, payload: dict):
        self.client.upsert(COLL, points=[qm.PointStruct(id=image_id, vector=img_vec, payload={
            "caption": caption,
            "confidence": caption_confidence,
            "origin": caption_origin,
            **payload,
        })])

    async def fetch_image(self, image_id: str):
        r = self.client.retrieve(COLL, ids=[image_id])
        return None if not r else {"id": image_id, **(r[0].payload or {})}

    async def search(self, query_vec, k: int = 10):
        res = self.client.search(COLL, query_vector=query_vec, limit=k)
        return [{"id": p.id, "score": float(p.score), **(p.payload or {})} for p in res]
