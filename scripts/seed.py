"""
Seed script to ingest images from a CSV/TSV list:
  url,tag
Use:  python scripts/seed.py data/seed_urls.csv
"""
import sys, csv, asyncio, httpx

async def ingest(url: str, tag: str|None=None):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get("http://localhost:8000/images", params={"url": url})
        r.raise_for_status()
        print(url, r.json().get("id"), tag)

async def main(p):
    tasks = []
    with open(p, newline="") as f:
        for row in csv.DictReader(f):
            tasks.append(ingest(row["url"], row.get("tag")))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed.py data/seed_urls.csv")
        raise SystemExit(2)
    asyncio.run(main(sys.argv[1]))
