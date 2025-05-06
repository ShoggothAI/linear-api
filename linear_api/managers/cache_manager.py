"""
Cache manager for Linear API.

This module provides centralized caching functionality for the Linear API client.
"""

import logging
import time
from typing import Any, Dict, Optional, TypeVar, Callable

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Cache manager for Linear API.

    This class provides methods for caching and retrieving values,
    with optional expiration times and cache invalidation.
    """

    def __init__(self, enabled: bool = True, default_ttl: int = 3600):
        """
        Initialize the cache manager.

        Args:
            enabled: Whether caching is enabled
            default_ttl: Default time-to-live for cached items in seconds (1 hour default)
        """
        self._enabled = enabled
        self._default_ttl = default_ttl
        self._caches: Dict[str, Dict[Any, tuple[Any, Optional[float]]]] = {}
        self._hit_count = 0
        self._miss_count = 0

    def get(self, cache_name: str, key: K) -> Optional[V]:
        """
        Get a value from the cache.

        Args:
            cache_name: The name of the cache
            key: The key to look up

        Returns:
            The cached value, or None if not found or expired
        """
        if not self._enabled:
            self._miss_count += 1
            return None

        # Initialize cache if it doesn't exist
        if cache_name not in self._caches:
            self._caches[cache_name] = {}
            self._miss_count += 1
            return None

        # Check if the key exists
        if key not in self._caches[cache_name]:
            self._miss_count += 1
            return None

        # Get the value and expiration time
        value, expiry = self._caches[cache_name][key]

        # Check if the value has expired
        if expiry is not None and time.time() > expiry:
            del self._caches[cache_name][key]
            self._miss_count += 1
            return None

        # Return the cached value
        self._hit_count += 1
        return value

    def set(self, cache_name: str, key: K, value: V, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.

        Args:
            cache_name: The name of the cache
            key: The key to store the value under
            value: The value to store
            ttl: Optional time-to-live in seconds
        """
        if not self._enabled:
            return

        # Initialize cache if it doesn't exist
        if cache_name not in self._caches:
            self._caches[cache_name] = {}

        # Calculate expiration time
        expiry = None
        if ttl is not None:
            expiry = time.time() + ttl
        elif self._default_ttl > 0:
            expiry = time.time() + self._default_ttl

        # Store the value
        self._caches[cache_name][key] = (value, expiry)

    def cached(self, cache_name: str, key_fn: Callable = lambda *args, **kwargs: str(args) + str(kwargs)):
        """
        Decorator for caching function results.

        Args:
            cache_name: The name of the cache
            key_fn: A function that generates a cache key from the function arguments

        Returns:
            A decorator function
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = key_fn(*args, **kwargs)

                # Try to get from cache
                cached_value = self.get(cache_name, key)
                if cached_value is not None:
                    return cached_value

                # Call the original function
                result = func(*args, **kwargs)

                # Cache the result
                self.set(cache_name, key, result)

                return result

            return wrapper

        return decorator

    def clear(self, cache_name: Optional[str] = None) -> None:
        """
        Clear a cache or all caches.

        Args:
            cache_name: The name of the cache to clear, or None to clear all caches
        """
        if cache_name is None:
            self._caches.clear()
            logger.debug("All caches cleared")
        elif cache_name in self._caches:
            self._caches[cache_name].clear()
            logger.debug(f"Cache '{cache_name}' cleared")

    def invalidate(self, cache_name: str, key: K) -> None:
        """
        Invalidate a specific cache entry.

        Args:
            cache_name: The name of the cache
            key: The key to invalidate
        """
        if not self._enabled or cache_name not in self._caches:
            return

        if key in self._caches[cache_name]:
            del self._caches[cache_name][key]
            logger.debug(f"Cache entry '{key}' invalidated from '{cache_name}'")

    def enable(self) -> None:
        """Enable caching."""
        self._enabled = True

    def disable(self) -> None:
        """Disable caching."""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set whether caching is enabled."""
        self._enabled = value

    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0

        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "cache_count": len(self._caches),
            "entry_counts": {cache_name: len(entries) for cache_name, entries in self._caches.items()}
        }

    def get_cache_size(self, cache_name: Optional[str] = None) -> int:
        """
        Get the number of entries in a cache or in all caches.

        Args:
            cache_name: The name of the cache, or None for all caches

        Returns:
            The number of entries in the specified cache(s)
        """
        if cache_name is None:
            return sum(len(cache) for cache in self._caches.values())
        elif cache_name in self._caches:
            return len(self._caches[cache_name])
        return 0
