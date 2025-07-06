"""Rate limiting utilities for API calls."""

import asyncio
import time
import logging
from typing import Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_concurrent: int = 10
    delay: float = 0.5
    max_retries: int = 3
    backoff_factor: float = 2.0


class RateLimiter:
    """
    Rate limiter for API calls with concurrent request limiting.
    """
    
    def __init__(
        self,
        max_concurrent: int = 10,
        delay: float = 0.5,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_concurrent: Maximum concurrent requests
            delay: Base delay between requests (seconds)
            max_retries: Maximum retry attempts
            backoff_factor: Exponential backoff factor
        """
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Semaphore for concurrent request limiting
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Track last request time for rate limiting
        self.last_request_time = 0.0
        
        # Statistics
        self.stats = {
            "requests_made": 0,
            "requests_delayed": 0,
            "concurrent_limit_hits": 0,
        }
    
    async def acquire(self) -> None:
        """
        Acquire rate limit permission.
        Must be called before making an API request.
        """
        # Wait for semaphore (concurrent limiting)
        await self.semaphore.acquire()
        
        try:
            # Calculate delay needed
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay:
                delay_needed = self.delay - time_since_last
                self.stats["requests_delayed"] += 1
                await asyncio.sleep(delay_needed)
            
            self.last_request_time = time.time()
            self.stats["requests_made"] += 1
            
        except Exception:
            # Release semaphore if something goes wrong
            self.semaphore.release()
            raise
    
    def release(self) -> None:
        """Release rate limit permission."""
        self.semaphore.release()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.release()
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry.
        
        Args:
            func: Async function to execute
            *args: Function positional arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Use rate limiter
                async with self:
                    return await func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate backoff delay
                    backoff_delay = self.delay * (self.backoff_factor ** attempt)
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {backoff_delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(f"API call failed after {self.max_retries + 1} attempts: {e}")
                    break
        
        # If we get here, all retries were exhausted
        raise last_exception
    
    def get_stats(self) -> dict:
        """Get rate limiting statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            "requests_made": 0,
            "requests_delayed": 0,
            "concurrent_limit_hits": 0,
        }


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for more sophisticated rate limiting.
    """
    
    def __init__(
        self,
        tokens_per_second: float = 1.0,
        bucket_size: int = 10,
        initial_tokens: Optional[int] = None,
    ):
        """
        Initialize token bucket rate limiter.
        
        Args:
            tokens_per_second: Rate of token replenishment
            bucket_size: Maximum tokens in bucket
            initial_tokens: Initial token count (defaults to bucket_size)
        """
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.tokens = initial_tokens if initial_tokens is not None else bucket_size
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
        """
        async with self.lock:
            await self._refill()
            
            # Wait until we have enough tokens
            while self.tokens < tokens:
                # Calculate how long to wait for tokens
                wait_time = (tokens - self.tokens) / self.tokens_per_second
                await asyncio.sleep(wait_time)
                await self._refill()
            
            # Consume tokens
            self.tokens -= tokens
    
    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        current_time = time.time()
        elapsed = current_time - self.last_update
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.tokens_per_second
        self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
        
        self.last_update = current_time
    
    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        return self.tokens