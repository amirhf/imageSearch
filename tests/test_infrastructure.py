"""
Test infrastructure components: utilities, rate limiter, and mock provider.
This test runs without requiring any API keys - perfect for CI/CD.
"""

import asyncio
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 > nul')
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass  # Ignore encoding errors in CI

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.services.utils.image_utils import (
    encode_image_base64,
    validate_image_bytes,
    get_image_info,
)
from apps.api.services.cloud_providers.rate_limiter import RateLimiter
from apps.api.services.cloud_providers.factory import CloudProviderFactory
from apps.api.services.cloud_providers.mock import MockCloudProvider


def test_image_utils():
    """Test image utility functions"""
    print("\n" + "="*60)
    print("TEST 1: Image Utilities")
    print("="*60)
    
    try:
        # Create a simple test image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='blue')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        img_bytes = buf.getvalue()
        
        print(f"✓ Created test image ({len(img_bytes)} bytes)")
        
        # Test validation
        is_valid, error = validate_image_bytes(img_bytes)
        assert is_valid, f"Image validation failed: {error}"
        print(f"✓ Image validation passed")
        
        # Test encoding
        b64 = encode_image_base64(img_bytes)
        assert len(b64) > 0
        print(f"✓ Base64 encoding successful ({len(b64)} chars)")
        
        # Test image info
        info = get_image_info(img_bytes)
        assert info['width'] == 100
        assert info['height'] == 100
        print(f"✓ Image info: {info['width']}x{info['height']}, {info['format']}, {info['size_bytes']} bytes")
        
        print("\n✅ Image utilities test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Image utilities test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rate_limiter():
    """Test rate limiter"""
    print("\n" + "="*60)
    print("TEST 2: Rate Limiter")
    print("="*60)
    
    try:
        # Create rate limiter with low limits for testing
        limiter = RateLimiter(
            max_per_minute=5,
            max_per_day=10,
            daily_budget_usd=0.01,
        )
        
        print(f"✓ Rate limiter created with limits: 5/min, 10/day, $0.01/day")
        
        # Test can proceed
        can_proceed, reason = limiter.can_proceed(estimated_cost_usd=0.001)
        assert can_proceed, f"Should be able to proceed: {reason}"
        print(f"✓ Initial check passed")
        
        # Record some requests
        for i in range(3):
            limiter.record_request(cost_usd=0.001)
        print(f"✓ Recorded 3 requests")
        
        # Check stats
        stats = limiter.get_stats()
        print(f"✓ Stats: {stats['requests_last_minute']}/min, {stats['requests_today']}/day, ${stats['cost_today_usd']}")
        assert stats['requests_last_minute'] == 3
        assert stats['cost_today_usd'] == 0.003
        
        # Test budget limit
        can_proceed, reason = limiter.can_proceed(estimated_cost_usd=0.02)
        assert not can_proceed, "Should block due to budget"
        print(f"✓ Budget limit works: {reason}")
        
        # Fill up minute limit
        for i in range(2):
            limiter.record_request(cost_usd=0.0001)
        can_proceed, reason = limiter.can_proceed(estimated_cost_usd=0.0001)
        assert not can_proceed, "Should block due to per-minute limit"
        print(f"✓ Per-minute limit works: {reason}")
        
        print("\n✅ Rate limiter test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Rate limiter test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_provider():
    """Test mock cloud provider"""
    print("\n" + "="*60)
    print("TEST 3: Mock Cloud Provider")
    print("="*60)
    
    try:
        # Create test image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (200, 200), color='red')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        img_bytes = buf.getvalue()
        
        print(f"✓ Created test image ({len(img_bytes)} bytes)")
        
        # Create mock provider
        provider = MockCloudProvider()
        assert provider.health_check()
        print(f"✓ Mock provider created and healthy")
        
        # Test caption generation
        print("⏳ Generating caption (this takes 1-3 seconds to simulate API latency)...")
        response = await provider.caption(img_bytes)
        
        assert response.caption is not None
        assert len(response.caption) > 10
        assert response.cost_usd > 0
        assert response.latency_ms > 0
        assert response.input_tokens > 0
        assert response.output_tokens > 0
        
        print(f"✓ Caption: '{response.caption}'")
        print(f"✓ Latency: {response.latency_ms}ms")
        print(f"✓ Cost: ${response.cost_usd}")
        print(f"✓ Tokens: {response.input_tokens} in, {response.output_tokens} out")
        print(f"✓ Model: {response.model}")
        
        print("\n✅ Mock provider test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Mock provider test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_factory():
    """Test cloud provider factory"""
    print("\n" + "="*60)
    print("TEST 4: Cloud Provider Factory")
    print("="*60)
    
    try:
        # List providers
        providers = CloudProviderFactory.list_providers()
        print(f"✓ Available providers: {providers}")
        
        # Get default provider
        default = CloudProviderFactory.get_default_provider()
        print(f"✓ Default provider: {default}")
        
        # Create mock provider via factory
        provider = CloudProviderFactory.create("mock")
        assert isinstance(provider, MockCloudProvider)
        print(f"✓ Created mock provider via factory")
        
        # Test it works
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color='green')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        img_bytes = buf.getvalue()
        
        print("⏳ Testing factory-created provider...")
        response = await provider.caption(img_bytes)
        assert response.caption is not None
        print(f"✓ Factory-created provider works: '{response.caption}'")
        
        print("\n✅ Factory test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Factory test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("INFRASTRUCTURE TESTS (CI/CD Safe)")
    print("="*60)
    print("\nTesting core infrastructure without API keys...")
    
    results = []
    
    # Run tests
    results.append(("Image Utilities", test_image_utils()))
    results.append(("Rate Limiter", test_rate_limiter()))
    results.append(("Mock Provider", await test_mock_provider()))
    results.append(("Provider Factory", await test_factory()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All infrastructure tests passed!")
        print("✓ Safe to run in CI/CD pipeline")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
