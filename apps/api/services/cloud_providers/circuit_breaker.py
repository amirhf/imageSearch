"""Circuit breaker for cloud provider fault tolerance"""

import time
import os
from enum import Enum
from typing import Optional


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation, requests allowed
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for cloud API calls.
    Prevents cascading failures by temporarily blocking requests when errors exceed threshold.
    """
    
    def __init__(
        self,
        failure_threshold: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        half_open_max_calls: int = 1,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold or int(
            os.getenv("CLOUD_CIRCUIT_BREAKER_THRESHOLD", 5)
        )
        self.timeout_seconds = timeout_seconds or int(
            os.getenv("CLOUD_CIRCUIT_BREAKER_TIMEOUT_SECONDS", 60)
        )
        self.half_open_max_calls = half_open_max_calls
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None
        self.half_open_calls = 0
        
        print(f"[CircuitBreaker] Initialized: threshold={self.failure_threshold}, timeout={self.timeout_seconds}s")
    
    def can_proceed(self) -> tuple[bool, Optional[str]]:
        """
        Check if request can proceed based on circuit state.
        
        Returns:
            Tuple of (can_proceed, reason_if_blocked)
        """
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            # Normal operation
            return True, None
        
        elif self.state == CircuitState.OPEN:
            # Check if timeout expired
            if self.opened_at and (current_time - self.opened_at) >= self.timeout_seconds:
                # Transition to half-open
                self._transition_to_half_open()
                return True, None
            else:
                remaining = self.timeout_seconds - int(current_time - self.opened_at) if self.opened_at else 0
                return False, f"Circuit breaker OPEN ({remaining}s remaining until retry)"
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited calls for testing
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True, None
            else:
                return False, "Circuit breaker HALF_OPEN (max test calls reached)"
        
        return False, "Unknown circuit state"
    
    def record_success(self):
        """Record a successful request"""
        if self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
        
        elif self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # If success in half-open, close the circuit
            print(f"[CircuitBreaker] Success in HALF_OPEN state, closing circuit")
            self._transition_to_closed()
    
    def record_failure(self):
        """Record a failed request"""
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # Failure in half-open, go back to open
            print(f"[CircuitBreaker] Failure in HALF_OPEN state, reopening circuit")
            self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        print(f"[CircuitBreaker] Circuit OPENED after {self.failure_count} failures (will retry in {self.timeout_seconds}s)")
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        print(f"[CircuitBreaker] Circuit HALF_OPEN (testing recovery)")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.opened_at = None
        print(f"[CircuitBreaker] Circuit CLOSED (service recovered)")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "timeout_seconds": self.timeout_seconds,
            "opened_at": self.opened_at,
            "last_failure_time": self.last_failure_time,
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        self._transition_to_closed()
        print(f"[CircuitBreaker] Manually reset")


# Global circuit breaker instance
_circuit_breaker = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get global circuit breaker instance"""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker
