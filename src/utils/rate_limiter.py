"""
Rate limiter implementation to prevent IP blocking by limiting request frequency
"""
import time
import threading
import logging
from typing import Dict, Any, Optional
from collections import deque
from datetime import datetime, timedelta

from src.config import get_config

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter that restricts the number of requests within a time period.
    Implements the Singleton pattern to ensure only one rate limiter exists.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        """Implement singleton pattern with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RateLimiter, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the rate limiter."""
        with self._lock:
            if self._initialized:
                return

            self.config = get_config()
            self.requests = deque()
            self.max_requests = self.config.get('rate_limit_requests', 10)
            self.period = self.config.get('rate_limit_period', 60)  # seconds
            self._initialized = True
            logger.info(
                f"Rate limiter initialized: {self.max_requests} requests per {self.period} seconds")

    def wait_if_needed(self, domain: str = "default") -> None:
        """
        Wait if the rate limit has been reached.

        Args:
            domain: The domain to rate limit (allows different limits for different domains)
        """
        with self._lock:
            now = time.time()

            # Remove requests older than the period
            while self.requests and self.requests[0] < now - self.period:
                self.requests.popleft()

            # If we've reached the limit, wait until we can make another request
            if len(self.requests) >= self.max_requests:
                wait_time = self.period - (now - self.requests[0])
                if wait_time > 0:
                    logger.info(
                        f"Rate limit reached. Waiting {wait_time:.2f} seconds before next request")
                    time.sleep(wait_time)
                    # After waiting, clean up old requests again
                    now = time.time()
                    while self.requests and self.requests[0] < now - self.period:
                        self.requests.popleft()

            # Add the current request
            self.requests.append(now)

    def record_request(self, domain: str = "default") -> None:
        """
        Record a request without waiting.

        Args:
            domain: The domain of the request
        """
        with self._lock:
            now = time.time()

            # Remove requests older than the period
            while self.requests and self.requests[0] < now - self.period:
                self.requests.popleft()

            # Add the current request
            self.requests.append(now)

    def get_remaining_quota(self, domain: str = "default") -> int:
        """
        Get the number of requests remaining in the current period.

        Args:
            domain: The domain to check

        Returns:
            int: Number of requests remaining
        """
        with self._lock:
            now = time.time()

            # Remove requests older than the period
            while self.requests and self.requests[0] < now - self.period:
                self.requests.popleft()

            return max(0, self.max_requests - len(self.requests))

    def update_limits(self, max_requests: Optional[int] = None, period: Optional[int] = None) -> None:
        """
        Update rate limiting parameters.

        Args:
            max_requests: Maximum number of requests in the period
            period: Time period in seconds
        """
        with self._lock:
            if max_requests is not None:
                self.max_requests = max_requests

            if period is not None:
                self.period = period

            logger.info(
                f"Rate limiter updated: {self.max_requests} requests per {self.period} seconds")


# Create a singleton instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """
    Get the rate limiter instance.

    Returns:
        RateLimiter: The rate limiter instance
    """
    return _rate_limiter
