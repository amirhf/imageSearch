"""
Generate test activity to populate Prometheus metrics and Grafana dashboard.
Uses mock provider - no API keys required.
"""

import asyncio
import sys
import os
from pathlib import Path
from PIL import Image
import io
import random

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment to use mock provider
os.environ["CLOUD_PROVIDER"] = "mock"
os.environ["USE_MOCK_MODELS"] = "true"

from apps.api.services.cloud_providers.factory import CloudProviderFactory
from apps.api.services.cloud_providers.circuit_breaker import get_circuit_breaker


def create_test_image(width=200, height=200, color=None):
    """Create a test image"""
    if color is None:
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan']
        color = random.choice(colors)
    
    img = Image.new('RGB', (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()


async def generate_successful_requests(count=20):
    """Generate successful cloud caption requests"""
    print(f"\n📊 Generating {count} successful requests...")
    
    provider = CloudProviderFactory.create()
    
    for i in range(count):
        try:
            img_bytes = create_test_image(
                width=random.randint(150, 300),
                height=random.randint(150, 300)
            )
            
            response = await provider.caption(img_bytes)
            print(f"  ✓ Request {i+1}/{count}: {response.caption[:40]}... (${response.cost_usd:.6f})")
            
            # Small delay to simulate realistic traffic
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Request {i+1}/{count} failed: {e}")


async def generate_rate_limit_blocks(count=5):
    """Generate requests that will be rate limited"""
    print(f"\n⚠️  Generating {count} requests to trigger rate limiting...")
    
    from apps.api.services.cloud_providers.rate_limiter import get_rate_limiter
    
    # Temporarily reduce rate limit
    rate_limiter = get_rate_limiter()
    original_limit = rate_limiter.max_per_minute
    rate_limiter.max_per_minute = 3  # Very low limit
    
    provider = CloudProviderFactory.create()
    
    blocked = 0
    success = 0
    
    for i in range(count):
        try:
            img_bytes = create_test_image()
            response = await provider.caption(img_bytes)
            success += 1
            print(f"  ✓ Request {i+1}/{count}: Allowed")
        except Exception as e:
            if "Rate limit" in str(e):
                blocked += 1
                print(f"  ⊘ Request {i+1}/{count}: Rate limited")
            else:
                print(f"  ✗ Request {i+1}/{count}: Error - {e}")
        
        await asyncio.sleep(0.3)
    
    # Restore original limit
    rate_limiter.max_per_minute = original_limit
    
    print(f"  Result: {success} allowed, {blocked} blocked")


async def generate_circuit_breaker_activity():
    """Generate activity to demonstrate circuit breaker"""
    print(f"\n🔌 Generating circuit breaker activity...")
    
    # Get the circuit breaker
    cb = get_circuit_breaker()
    
    # Simulate some failures
    print("  Simulating failures...")
    for i in range(3):
        cb.record_failure()
        print(f"  ✗ Failure {i+1} recorded (state: {cb.state.value})")
        await asyncio.sleep(0.5)
    
    # Check if circuit opened
    can_proceed, reason = cb.can_proceed()
    if not can_proceed:
        print(f"  ⊘ Circuit breaker OPENED: {reason}")
    
    # Wait a bit and try recovery
    print("  Waiting 3 seconds for recovery window...")
    await asyncio.sleep(3)
    
    can_proceed, reason = cb.can_proceed()
    print(f"  State after timeout: {cb.state.value}")
    
    if can_proceed:
        cb.record_success()
        print(f"  ✓ Recovery successful (state: {cb.state.value})")


async def generate_varied_traffic():
    """Generate varied traffic patterns"""
    print(f"\n🌊 Generating varied traffic patterns...")
    
    provider = CloudProviderFactory.create()
    
    # Mix of different image sizes
    sizes = [(100, 100), (200, 200), (300, 300), (150, 200), (250, 150)]
    
    for i, (width, height) in enumerate(sizes * 2):  # 10 requests
        try:
            img_bytes = create_test_image(width=width, height=height)
            response = await provider.caption(img_bytes)
            print(f"  ✓ Request {i+1}/10: {width}x{height} → {response.latency_ms}ms")
            await asyncio.sleep(random.uniform(0.3, 1.0))
        except Exception as e:
            print(f"  ✗ Request {i+1}/10 failed: {e}")


async def main():
    """Generate comprehensive test data for metrics"""
    print("="*60)
    print("GENERATING METRICS DATA FOR GRAFANA")
    print("="*60)
    print("\nThis will populate Prometheus metrics with test data.")
    print("You can then view the data in Grafana dashboard.")
    print("")
    
    try:
        # 1. Generate successful requests
        await generate_successful_requests(count=25)
        
        # 2. Generate some rate limit blocks
        await generate_rate_limit_blocks(count=10)
        
        # 3. Generate circuit breaker activity
        await generate_circuit_breaker_activity()
        
        # 4. Generate varied traffic
        await generate_varied_traffic()
        
        # 5. Final burst of successful requests
        print(f"\n🚀 Final burst of requests...")
        await generate_successful_requests(count=15)
        
        print("\n" + "="*60)
        print("✅ METRICS GENERATION COMPLETE!")
        print("="*60)
        print("\nMetrics have been generated and recorded.")
        print("\nNext steps:")
        print("  1. Check Prometheus: http://localhost:9090/graph")
        print("     Try query: cloud_requests_total")
        print("")
        print("  2. View Grafana dashboard: http://localhost:3000")
        print("     Dashboard: Cloud Caption Adapter")
        print("")
        print("  3. Wait 15-30 seconds for Prometheus to scrape metrics")
        print("     (if API is running on port 8000)")
        
    except Exception as e:
        print(f"\n❌ Error generating metrics: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
