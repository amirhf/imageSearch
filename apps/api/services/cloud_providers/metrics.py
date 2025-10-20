"""
Prometheus metrics for cloud caption provider monitoring.
Provides comprehensive observability for cost, performance, and reliability.
"""

import time
from functools import wraps
from typing import Optional, Callable
from contextlib import contextmanager

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("[WARN] prometheus_client not available - metrics disabled")


class CloudMetrics:
    """
    Centralized metrics collection for cloud caption providers.
    Tracks requests, costs, performance, and system health.
    """
    
    def __init__(self):
        """Initialize Prometheus metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # ============================================================
        # REQUEST METRICS
        # ============================================================
        
        self.requests_total = Counter(
            'cloud_requests_total',
            'Total number of cloud caption requests',
            ['provider', 'model', 'status']
        )
        
        self.requests_failed_total = Counter(
            'cloud_requests_failed_total',
            'Total number of failed cloud requests',
            ['provider', 'model', 'reason']
        )
        
        self.requests_in_flight = Gauge(
            'cloud_requests_in_flight',
            'Number of cloud requests currently in progress',
            ['provider']
        )
        
        # ============================================================
        # PERFORMANCE METRICS
        # ============================================================
        
        self.request_duration_seconds = Histogram(
            'cloud_request_duration_seconds',
            'Cloud request duration in seconds',
            ['provider', 'model'],
            buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.request_size_bytes = Histogram(
            'cloud_request_size_bytes',
            'Cloud request payload size in bytes',
            ['provider'],
            buckets=[1000, 5000, 10000, 50000, 100000, 500000, 1000000]
        )
        
        self.response_size_bytes = Histogram(
            'cloud_response_size_bytes',
            'Cloud response size in bytes',
            ['provider'],
            buckets=[100, 500, 1000, 5000, 10000]
        )
        
        # ============================================================
        # COST METRICS
        # ============================================================
        
        self.cost_total_usd = Counter(
            'cloud_cost_total_usd',
            'Total cost in USD for cloud requests',
            ['provider', 'model']
        )
        
        self.daily_cost_usd = Gauge(
            'cloud_daily_cost_usd',
            'Current daily cost in USD',
            ['provider']
        )
        
        self.daily_budget_remaining_usd = Gauge(
            'cloud_daily_budget_remaining_usd',
            'Remaining daily budget in USD',
            ['provider']
        )
        
        self.tokens_input_total = Counter(
            'cloud_tokens_input_total',
            'Total input tokens processed',
            ['provider', 'model']
        )
        
        self.tokens_output_total = Counter(
            'cloud_tokens_output_total',
            'Total output tokens generated',
            ['provider', 'model']
        )
        
        # ============================================================
        # RATE LIMITER METRICS
        # ============================================================
        
        self.rate_limiter_requests_allowed = Counter(
            'rate_limiter_requests_allowed_total',
            'Total requests allowed by rate limiter'
        )
        
        self.rate_limiter_requests_blocked = Counter(
            'rate_limiter_requests_blocked_total',
            'Total requests blocked by rate limiter',
            ['reason']
        )
        
        self.rate_limiter_requests_per_minute = Gauge(
            'rate_limiter_requests_per_minute',
            'Current requests per minute'
        )
        
        self.rate_limiter_requests_today = Gauge(
            'rate_limiter_requests_today',
            'Total requests today'
        )
        
        self.rate_limiter_budget_used_usd = Gauge(
            'rate_limiter_budget_used_usd',
            'Budget used today in USD'
        )
        
        self.rate_limiter_budget_remaining_usd = Gauge(
            'rate_limiter_budget_remaining_usd',
            'Budget remaining today in USD'
        )
        
        # ============================================================
        # CIRCUIT BREAKER METRICS
        # ============================================================
        
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half_open)'
        )
        
        self.circuit_breaker_opened_total = Counter(
            'circuit_breaker_opened_total',
            'Total times circuit breaker opened'
        )
        
        self.circuit_breaker_success_total = Counter(
            'circuit_breaker_success_total',
            'Total successful requests through circuit breaker'
        )
        
        self.circuit_breaker_failure_total = Counter(
            'circuit_breaker_failure_total',
            'Total failed requests causing circuit breaker action'
        )
        
        self.circuit_breaker_rejected_total = Counter(
            'circuit_breaker_rejected_total',
            'Total requests rejected by circuit breaker'
        )
        
        # ============================================================
        # CAPTION QUALITY METRICS
        # ============================================================
        
        self.caption_source_total = Counter(
            'caption_source_total',
            'Total captions by source',
            ['source']  # local or cloud
        )
        
        self.caption_confidence = Histogram(
            'caption_confidence',
            'Caption confidence scores',
            ['source'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        self.caption_length_chars = Histogram(
            'caption_length_chars',
            'Caption length in characters',
            ['source'],
            buckets=[10, 20, 50, 100, 200, 500]
        )
        
        self.caption_cloud_fallback_rate = Gauge(
            'caption_cloud_fallback_rate',
            'Rate of fallback to cloud captions (0.0-1.0)'
        )
    
    # ============================================================
    # REQUEST TRACKING
    # ============================================================
    
    def record_request(
        self,
        provider: str,
        model: str,
        status: str,
        duration_seconds: float,
        cost_usd: float,
        input_tokens: int,
        output_tokens: int,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
    ):
        """
        Record a completed cloud request with all metrics.
        
        Args:
            provider: Provider name (e.g., 'openrouter')
            model: Model name (e.g., 'openai/gpt-4o-mini')
            status: Request status ('success', 'error')
            duration_seconds: Request duration in seconds
            cost_usd: Request cost in USD
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            request_size_bytes: Request payload size
            response_size_bytes: Response size
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Request metrics
        self.requests_total.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()
        
        # Performance metrics
        self.request_duration_seconds.labels(
            provider=provider,
            model=model
        ).observe(duration_seconds)
        
        if request_size_bytes:
            self.request_size_bytes.labels(provider=provider).observe(request_size_bytes)
        
        if response_size_bytes:
            self.response_size_bytes.labels(provider=provider).observe(response_size_bytes)
        
        # Cost metrics
        if status == 'success':
            self.cost_total_usd.labels(
                provider=provider,
                model=model
            ).inc(cost_usd)
            
            self.tokens_input_total.labels(
                provider=provider,
                model=model
            ).inc(input_tokens)
            
            self.tokens_output_total.labels(
                provider=provider,
                model=model
            ).inc(output_tokens)
    
    def record_failure(
        self,
        provider: str,
        model: str,
        reason: str
    ):
        """Record a failed request"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.requests_failed_total.labels(
            provider=provider,
            model=model,
            reason=reason
        ).inc()
    
    @contextmanager
    def track_request(self, provider: str):
        """
        Context manager to track in-flight requests.
        
        Usage:
            with metrics.track_request('openrouter'):
                response = await api_call()
        """
        if PROMETHEUS_AVAILABLE:
            self.requests_in_flight.labels(provider=provider).inc()
        
        try:
            yield
        finally:
            if PROMETHEUS_AVAILABLE:
                self.requests_in_flight.labels(provider=provider).dec()
    
    # ============================================================
    # RATE LIMITER TRACKING
    # ============================================================
    
    def record_rate_limit_allowed(self):
        """Record a request allowed by rate limiter"""
        if not PROMETHEUS_AVAILABLE:
            return
        self.rate_limiter_requests_allowed.inc()
    
    def record_rate_limit_blocked(self, reason: str):
        """Record a request blocked by rate limiter"""
        if not PROMETHEUS_AVAILABLE:
            return
        self.rate_limiter_requests_blocked.labels(reason=reason).inc()
    
    def update_rate_limiter_stats(
        self,
        requests_per_minute: int,
        requests_today: int,
        budget_used_usd: float,
        budget_remaining_usd: float
    ):
        """Update rate limiter gauges"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.rate_limiter_requests_per_minute.set(requests_per_minute)
        self.rate_limiter_requests_today.set(requests_today)
        self.rate_limiter_budget_used_usd.set(budget_used_usd)
        self.rate_limiter_budget_remaining_usd.set(budget_remaining_usd)
    
    # ============================================================
    # CIRCUIT BREAKER TRACKING
    # ============================================================
    
    def update_circuit_breaker_state(self, state: str):
        """
        Update circuit breaker state gauge.
        
        Args:
            state: 'closed', 'open', or 'half_open'
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        state_map = {'closed': 0, 'open': 1, 'half_open': 2}
        self.circuit_breaker_state.set(state_map.get(state, 0))
    
    def record_circuit_breaker_opened(self):
        """Record circuit breaker opening"""
        if not PROMETHEUS_AVAILABLE:
            return
        self.circuit_breaker_opened_total.inc()
    
    def record_circuit_breaker_success(self):
        """Record successful request through circuit breaker"""
        if not PROMETHEUS_AVAILABLE:
            return
        self.circuit_breaker_success_total.inc()
    
    def record_circuit_breaker_failure(self):
        """Record failed request through circuit breaker"""
        if not PROMETHEUS_AVAILABLE:
            return
        self.circuit_breaker_failure_total.inc()
    
    def record_circuit_breaker_rejected(self):
        """Record request rejected by circuit breaker"""
        if not PROMETHEUS_AVAILABLE:
            return
        self.circuit_breaker_rejected_total.inc()
    
    # ============================================================
    # CAPTION QUALITY TRACKING
    # ============================================================
    
    def record_caption(
        self,
        source: str,
        confidence: Optional[float] = None,
        length_chars: Optional[int] = None
    ):
        """
        Record a caption generation.
        
        Args:
            source: 'local' or 'cloud'
            confidence: Caption confidence score (0.0-1.0)
            length_chars: Caption length in characters
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.caption_source_total.labels(source=source).inc()
        
        if confidence is not None:
            self.caption_confidence.labels(source=source).observe(confidence)
        
        if length_chars is not None:
            self.caption_length_chars.labels(source=source).observe(length_chars)
    
    def update_cloud_fallback_rate(self, rate: float):
        """Update cloud fallback rate (0.0-1.0)"""
        if not PROMETHEUS_AVAILABLE:
            return
        self.caption_cloud_fallback_rate.set(rate)
    
    # ============================================================
    # DAILY COST UPDATES
    # ============================================================
    
    def update_daily_cost(
        self,
        provider: str,
        cost_usd: float,
        budget_remaining_usd: float
    ):
        """Update daily cost gauges"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.daily_cost_usd.labels(provider=provider).set(cost_usd)
        self.daily_budget_remaining_usd.labels(provider=provider).set(budget_remaining_usd)


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_metrics = None


def get_metrics() -> CloudMetrics:
    """Get global metrics instance"""
    global _metrics
    if _metrics is None:
        _metrics = CloudMetrics()
    return _metrics


# ============================================================
# DECORATOR FOR AUTOMATIC METRIC RECORDING
# ============================================================

def track_cloud_request(provider: str, model: str):
    """
    Decorator to automatically track cloud request metrics.
    
    Usage:
        @track_cloud_request('openrouter', 'gpt-4o-mini')
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start = time.time()
            
            with metrics.track_request(provider):
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start
                    
                    # Extract metrics from result if it's a CloudCaptionResponse
                    if hasattr(result, 'cost_usd'):
                        metrics.record_request(
                            provider=provider,
                            model=model,
                            status='success',
                            duration_seconds=duration,
                            cost_usd=result.cost_usd,
                            input_tokens=result.input_tokens,
                            output_tokens=result.output_tokens,
                        )
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start
                    metrics.record_failure(
                        provider=provider,
                        model=model,
                        reason=type(e).__name__
                    )
                    raise
        
        return wrapper
    return decorator
