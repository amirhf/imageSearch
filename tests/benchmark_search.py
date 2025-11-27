import asyncio
import time
import httpx
import os
import sys
from pathlib import Path
import statistics
from jose import jwt
from datetime import datetime, timedelta
import uuid

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

BASE_URL = "http://localhost:8000"

def create_test_token(user_id: str, email: str, role: str = "user") -> str:
    """Create a test JWT token"""
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise ValueError("SUPABASE_JWT_SECRET not found in environment")
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, secret, algorithm="HS256")

async def benchmark_endpoint(name: str, url: str, headers: dict = None, iterations: int = 50):
    print(f"\nBenchmarking {name} ({iterations} iterations)...")
    latencies = []
    
    async with httpx.AsyncClient() as client:
        # Warmup
        await client.get(url, headers=headers)
        
        start_total = time.time()
        for _ in range(iterations):
            start = time.time()
            resp = await client.get(url, headers=headers)
            latencies.append((time.time() - start) * 1000) # ms
            if resp.status_code != 200:
                print(f"Error: {resp.status_code} - {resp.text}")
        
        total_time = time.time() - start_total
        
    avg_lat = statistics.mean(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18] # 95th percentile
    p99_lat = statistics.quantiles(latencies, n=100)[98] # 99th percentile
    rps = iterations / total_time
    
    print(f"  Avg Latency: {avg_lat:.2f} ms")
    print(f"  P95 Latency: {p95_lat:.2f} ms")
    print(f"  P99 Latency: {p99_lat:.2f} ms")
    print(f"  Throughput:  {rps:.2f} req/sec")
    
    return {
        "name": name,
        "avg_ms": avg_lat,
        "p95_ms": p95_lat,
        "p99_ms": p99_lat,
        "rps": rps
    }

async def main():
    print("="*60)
    print("SEARCH PERFORMANCE BENCHMARK")
    print("="*60)
    
    # Ensure we have some data (optional, but good for real results)
    # For now, we assume the DB has whatever the user put in it.
    
    user_id = str(uuid.uuid4())
    token = create_test_token(user_id, "user1@test.com")
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    results = []
    
    # 1. Public Vector Search (No Auth)
    results.append(await benchmark_endpoint(
        "Public Vector Search", 
        f"{BASE_URL}/search?q=test&scope=public"
    ))
    
    # 2. Authenticated Hybrid Search (Scope=All)
    results.append(await benchmark_endpoint(
        "Auth Hybrid Search (Scope=All)", 
        f"{BASE_URL}/search?q=cat&scope=all",
        headers=auth_headers
    ))
    
    # 3. Authenticated Hybrid Search (Scope=Mine)
    results.append(await benchmark_endpoint(
        "Auth Hybrid Search (Scope=Mine)", 
        f"{BASE_URL}/search?q=cat&scope=mine",
        headers=auth_headers
    ))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Test Case':<30} | {'Avg (ms)':<10} | {'P95 (ms)':<10} | {'RPS':<10}")
    print("-" * 70)
    for r in results:
        print(f"{r['name']:<30} | {r['avg_ms']:<10.2f} | {r['p95_ms']:<10.2f} | {r['rps']:<10.2f}")

if __name__ == "__main__":
    asyncio.run(main())
