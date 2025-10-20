"""Rate limiter for cloud API calls to prevent cost overruns"""

import time
import os
from collections import deque
from typing import Optional

try:
    from .metrics import get_metrics
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


class RateLimiter:
    """
    Rate limiter with per-minute, per-day, and budget controls.
    Thread-safe for single-process usage.
    """
    
    def __init__(
        self,
        max_per_minute: Optional[int] = None,
        max_per_day: Optional[int] = None,
        daily_budget_usd: Optional[float] = None,
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_per_minute: Maximum requests per minute (default from env)
            max_per_day: Maximum requests per day (default from env)
            daily_budget_usd: Maximum daily spend in USD (default from env)
        """
        self.max_per_minute = max_per_minute or int(os.getenv("CLOUD_MAX_REQUESTS_PER_MINUTE", 60))
        self.max_per_day = max_per_day or int(os.getenv("CLOUD_MAX_REQUESTS_PER_DAY", 10000))
        self.daily_budget_usd = daily_budget_usd or float(os.getenv("CLOUD_DAILY_BUDGET_USD", 10.0))
        
        # Request tracking
        self.minute_requests = deque()  # Timestamps of requests in last minute
        self.daily_requests = []  # All requests today
        self.daily_cost = 0.0  # Total cost today
        self.last_reset = time.time()  # Last daily reset time
        
        # Metrics
        self.metrics = get_metrics() if METRICS_AVAILABLE else None
    
    def _reset_daily_if_needed(self):
        """Reset daily counters if 24 hours have passed"""
        now = time.time()
        if now - self.last_reset > 86400:  # 24 hours
            self.daily_requests = []
            self.daily_cost = 0.0
            self.last_reset = now
    
    def can_proceed(self, estimated_cost_usd: float = 0.001) -> tuple[bool, Optional[str]]:
        """
        Check if request can proceed based on limits.
        
        Args:
            estimated_cost_usd: Estimated cost of the request
            
        Returns:
            Tuple of (can_proceed, reason_if_blocked)
        """
        now = time.time()
        self._reset_daily_if_needed()
        
        # Check daily budget
        if self.daily_cost + estimated_cost_usd > self.daily_budget_usd:
            remaining = max(0, self.daily_budget_usd - self.daily_cost)
            reason = f"Daily budget exceeded (${self.daily_cost:.4f}/${self.daily_budget_usd}, ${remaining:.4f} remaining)"
            if self.metrics:
                self.metrics.record_rate_limit_blocked('budget')
            return False, reason
        
        # Check per-minute limit
        self.minute_requests = deque([t for t in self.minute_requests if now - t < 60])
        if len(self.minute_requests) >= self.max_per_minute:
            reason = f"Per-minute limit exceeded ({len(self.minute_requests)}/{self.max_per_minute})"
            if self.metrics:
                self.metrics.record_rate_limit_blocked('per_minute')
            return False, reason
        
        # Check per-day limit
        if len(self.daily_requests) >= self.max_per_day:
            reason = f"Per-day limit exceeded ({len(self.daily_requests)}/{self.max_per_day})"
            if self.metrics:
                self.metrics.record_rate_limit_blocked('per_day')
            return False, reason
        
        # Request allowed
        if self.metrics:
            self.metrics.record_rate_limit_allowed()
        
        return True, None
    
    def record_request(self, cost_usd: float = 0.0):
        """
        Record a successful request.
        
        Args:
            cost_usd: Actual cost of the request
        """
        now = time.time()
        self.minute_requests.append(now)
        self.daily_requests.append(now)
        self.daily_cost += cost_usd
        
        # Update metrics
        if self.metrics:
            self._update_metrics()
    
    def get_stats(self) -> dict:
        """
        Get current rate limiter statistics.
        
        Returns:
            Dictionary with current usage stats
        """
        now = time.time()
        self._reset_daily_if_needed()
        
        # Clean up minute requests
        self.minute_requests = deque([t for t in self.minute_requests if now - t < 60])
        
        return {
            "requests_last_minute": len(self.minute_requests),
            "requests_today": len(self.daily_requests),
            "cost_today_usd": round(self.daily_cost, 4),
            "limits": {
                "max_per_minute": self.max_per_minute,
                "max_per_day": self.max_per_day,
                "daily_budget_usd": self.daily_budget_usd,
            },
            "remaining": {
                "budget_usd": round(max(0, self.daily_budget_usd - self.daily_cost), 4),
                "requests_today": max(0, self.max_per_day - len(self.daily_requests)),
            }
        }
    
    def _update_metrics(self):
        """Update Prometheus metrics with current state"""
        if not self.metrics:
            return
        
        # Clean up minute requests
        now = time.time()
        self.minute_requests = deque([t for t in self.minute_requests if now - t < 60])
        
        # Update gauges
        self.metrics.update_rate_limiter_stats(
            requests_per_minute=len(self.minute_requests),
            requests_today=len(self.daily_requests),
            budget_used_usd=self.daily_cost,
            budget_remaining_usd=max(0, self.daily_budget_usd - self.daily_cost)
        )


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
