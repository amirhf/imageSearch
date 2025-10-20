"""
OpenTelemetry tracing helpers for cloud caption provider.
Provides distributed tracing for debugging and performance analysis.
"""

import time
from functools import wraps
from typing import Optional, Callable, Dict, Any
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    TRACING_AVAILABLE = True
    tracer = trace.get_tracer(__name__)
except ImportError:
    TRACING_AVAILABLE = False
    print("[WARN] opentelemetry-api not available - tracing disabled")


class CloudTracing:
    """
    Centralized tracing for cloud caption providers.
    Creates spans for key operations with relevant attributes.
    """
    
    def __init__(self):
        """Initialize tracing"""
        self.enabled = TRACING_AVAILABLE
    
    @contextmanager
    def trace_cloud_caption(
        self,
        provider: str,
        model: str,
        image_size_bytes: int,
    ):
        """
        Create a span for cloud caption request.
        
        Usage:
            with tracing.trace_cloud_caption('openrouter', 'gpt-4o-mini', 12345):
                response = await provider.caption(img_bytes)
        
        Args:
            provider: Provider name (e.g., 'openrouter')
            model: Model name (e.g., 'openai/gpt-4o-mini')
            image_size_bytes: Size of image in bytes
        """
        if not self.enabled:
            yield None
            return
        
        with tracer.start_as_current_span(
            "cloud_caption",
            attributes={
                "cloud.provider": provider,
                "cloud.model": model,
                "image.size_bytes": image_size_bytes,
            }
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @contextmanager
    def trace_rate_limit_check(self):
        """
        Create a span for rate limiter check.
        
        Usage:
            with tracing.trace_rate_limit_check() as span:
                can_proceed, reason = rate_limiter.can_proceed()
                if span:
                    span.set_attribute('can_proceed', can_proceed)
        """
        if not self.enabled:
            yield None
            return
        
        with tracer.start_as_current_span("rate_limit_check") as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    @contextmanager
    def trace_circuit_breaker_check(self):
        """
        Create a span for circuit breaker check.
        
        Usage:
            with tracing.trace_circuit_breaker_check() as span:
                can_proceed, reason = cb.can_proceed()
                if span:
                    span.set_attribute('state', cb.state.value)
        """
        if not self.enabled:
            yield None
            return
        
        with tracer.start_as_current_span("circuit_breaker_check") as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def add_event(self, span, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to a span.
        
        Args:
            span: OpenTelemetry span (or None if tracing disabled)
            name: Event name
            attributes: Optional event attributes
        """
        if span is not None and self.enabled:
            span.add_event(name, attributes=attributes or {})
    
    def set_attributes(self, span, attributes: Dict[str, Any]):
        """
        Set multiple attributes on a span.
        
        Args:
            span: OpenTelemetry span (or None if tracing disabled)
            attributes: Dictionary of attributes to set
        """
        if span is not None and self.enabled:
            for key, value in attributes.items():
                span.set_attribute(key, value)
    
    def set_status_ok(self, span):
        """Mark span as successful"""
        if span is not None and self.enabled:
            span.set_status(Status(StatusCode.OK))
    
    def set_status_error(self, span, message: str):
        """Mark span as failed"""
        if span is not None and self.enabled:
            span.set_status(Status(StatusCode.ERROR, message))


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_tracing = None


def get_tracing() -> CloudTracing:
    """Get global tracing instance"""
    global _tracing
    if _tracing is None:
        _tracing = CloudTracing()
    return _tracing


# ============================================================
# DECORATOR FOR AUTOMATIC TRACING
# ============================================================

def trace_operation(operation_name: str, **default_attributes):
    """
    Decorator to automatically trace an operation.
    
    Usage:
        @trace_operation('process_image', service='captioner')
        async def process_image(img_bytes):
            ...
    
    Args:
        operation_name: Name of the operation/span
        **default_attributes: Default attributes to add to span
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not TRACING_AVAILABLE:
                return await func(*args, **kwargs)
            
            with tracer.start_as_current_span(
                operation_name,
                attributes=default_attributes
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not TRACING_AVAILABLE:
                return func(*args, **kwargs)
            
            with tracer.start_as_current_span(
                operation_name,
                attributes=default_attributes
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def add_span_attributes(**attributes):
    """
    Add attributes to the current active span.
    
    Usage:
        add_span_attributes(user_id=123, request_type='caption')
    """
    if not TRACING_AVAILABLE:
        return
    
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, **attributes):
    """
    Add an event to the current active span.
    
    Usage:
        add_span_event('cache_miss', cache_key='image_123')
    """
    if not TRACING_AVAILABLE:
        return
    
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes=attributes)


def record_exception_in_span(exception: Exception):
    """
    Record an exception in the current active span.
    
    Usage:
        try:
            ...
        except Exception as e:
            record_exception_in_span(e)
            raise
    """
    if not TRACING_AVAILABLE:
        return
    
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


def get_trace_context() -> Optional[Dict[str, str]]:
    """
    Get current trace context for propagation.
    
    Returns:
        Dictionary with trace context headers, or None if not available
    """
    if not TRACING_AVAILABLE:
        return None
    
    try:
        from opentelemetry.propagate import inject
        carrier = {}
        inject(carrier)
        return carrier
    except:
        return None
