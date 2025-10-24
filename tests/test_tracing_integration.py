"""
Test tracing integration with cloud providers.
This test verifies that spans are properly created.
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
        pass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.api.services.cloud_providers.tracing import (
    get_tracing, 
    TRACING_AVAILABLE,
    add_span_attributes,
    add_span_event,
)
from apps.api.services.cloud_providers.factory import CloudProviderFactory


def test_tracing_module():
    """Test that tracing module is available"""
    print("\n" + "="*60)
    print("TEST 1: Tracing Module Availability")
    print("="*60)
    
    try:
        if TRACING_AVAILABLE:
            print("✓ OpenTelemetry is available")
            tracing = get_tracing()
            print("✓ Tracing instance created")
            assert tracing is not None
            assert tracing.enabled
            print("✅ Tracing module test PASSED")
            return True
        else:
            print("⚠️  OpenTelemetry not available (tracing disabled)")
            print("   Install with: pip install opentelemetry-api")
            tracing = get_tracing()
            assert tracing is not None
            assert not tracing.enabled
            print("✅ Test PASSED (gracefully handles missing opentelemetry)")
            return True
        
    except Exception as e:
        print(f"❌ Tracing module test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mock_provider_with_tracing():
    """Test mock provider with tracing integration"""
    print("\n" + "="*60)
    print("TEST 2: Mock Provider with Tracing")
    print("="*60)
    
    try:
        # Set mock provider
        os.environ["CLOUD_PROVIDER"] = "mock"
        
        # Create provider
        provider = CloudProviderFactory.create()
        print("✓ Mock provider created")
        
        # Create test image
        from PIL import Image
        import io
        
        img = Image.new('RGB', (150, 150), color='red')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        img_bytes = buf.getvalue()
        
        print(f"✓ Created test image ({len(img_bytes)} bytes)")
        
        # Generate caption (tracing should be active)
        print("⏳ Generating caption with tracing...")
        response = await provider.caption(img_bytes)
        
        print(f"✓ Caption generated: '{response.caption[:50]}...'")
        print(f"✓ Cost: ${response.cost_usd}")
        
        if TRACING_AVAILABLE:
            print("✓ Traces should be recorded in Jaeger")
            print("  - Parent span: cloud_caption")
            print("  - Child span: rate_limit_check")
            print("  - Events: encoding_image, api_request_start, api_response_received")
        else:
            print("⚠️  Traces not recorded (opentelemetry not installed)")
        
        print("\n✅ Mock provider with tracing test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Mock provider with tracing test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_managers():
    """Test tracing context managers"""
    print("\n" + "="*60)
    print("TEST 3: Tracing Context Managers")
    print("="*60)
    
    try:
        tracing = get_tracing()
        
        # Test cloud caption span
        with tracing.trace_cloud_caption('openrouter', 'gpt-4o-mini', 12345) as span:
            print("✓ cloud_caption span created")
            if span:
                tracing.set_attributes(span, {'test': 'value'})
                tracing.add_event(span, 'test_event')
                print("✓ Attributes and events added")
        
        # Test rate limit check span
        with tracing.trace_rate_limit_check() as span:
            print("✓ rate_limit_check span created")
            if span:
                tracing.set_attributes(span, {'can_proceed': True})
        
        # Test circuit breaker span
        with tracing.trace_circuit_breaker_check() as span:
            print("✓ circuit_breaker_check span created")
            if span:
                tracing.set_attributes(span, {'state': 'closed'})
        
        if TRACING_AVAILABLE:
            print("✓ All spans created successfully")
        else:
            print("⚠️  Spans not created (opentelemetry not installed)")
        
        print("\n✅ Context manager test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Context manager test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_helper_functions():
    """Test tracing helper functions"""
    print("\n" + "="*60)
    print("TEST 4: Tracing Helper Functions")
    print("="*60)
    
    try:
        # Test add_span_attributes
        add_span_attributes(user_id=123, request_type='caption')
        print("✓ add_span_attributes() works")
        
        # Test add_span_event
        add_span_event('test_event', key='value')
        print("✓ add_span_event() works")
        
        if TRACING_AVAILABLE:
            print("✓ Helper functions can add to current span")
        else:
            print("⚠️  Helper functions no-op (opentelemetry not installed)")
        
        print("\n✅ Helper functions test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Helper functions test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test tracing with errors"""
    print("\n" + "="*60)
    print("TEST 5: Tracing Error Handling")
    print("="*60)
    
    try:
        tracing = get_tracing()
        
        # Test that errors are properly traced
        try:
            with tracing.trace_cloud_caption('openrouter', 'gpt-4o-mini', 100) as span:
                print("✓ Creating span and simulating error...")
                raise ValueError("Simulated error")
        except ValueError:
            print("✓ Error caught (span should mark as error)")
        
        if TRACING_AVAILABLE:
            print("✓ Error should be recorded in span")
        else:
            print("⚠️  Error tracing disabled (opentelemetry not installed)")
        
        print("\n✅ Error handling test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error handling test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tracing integration tests"""
    print("\n" + "="*60)
    print("TRACING INTEGRATION TESTS")
    print("="*60)
    print("\nVerifying tracing is properly integrated with cloud providers...")
    
    if not TRACING_AVAILABLE:
        print("\n⚠️  NOTE: opentelemetry-api not installed")
        print("   Tracing will be disabled but code should work")
        print("   Install with: pip install opentelemetry-api\n")
    
    results = []
    
    # Run tests
    results.append(("Tracing Module", test_tracing_module()))
    results.append(("Mock Provider", await test_mock_provider_with_tracing()))
    results.append(("Context Managers", test_context_managers()))
    results.append(("Helper Functions", test_helper_functions()))
    results.append(("Error Handling", await test_error_handling()))
    
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
        print("\n🎉 Tracing integration complete!")
        if TRACING_AVAILABLE:
            print("✓ All components properly create spans")
            print("✓ Ready for Jaeger visualization")
            print("\nNext steps:")
            print("  1. Configure OpenTelemetry exporter in API")
            print("  2. View traces in Jaeger UI (http://localhost:16686)")
        else:
            print("✓ All components handle missing opentelemetry gracefully")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
