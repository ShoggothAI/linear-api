"""
Tests for the CacheManager class.

This module tests the functionality of the centralized caching system.
"""

import pytest
import time
from linear_api import LinearClient
from linear_api.managers.cache_manager import CacheManager


@pytest.fixture
def client():
    """Create a LinearClient instance for testing."""
    # Get the API key from environment variable
    import os
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        pytest.skip("LINEAR_API_KEY environment variable not set")

    # Create and return the client with caching enabled
    return LinearClient(api_key=api_key, enable_cache=True, cache_ttl=60)


@pytest.fixture
def cache_manager():
    """Create a standalone CacheManager for testing."""
    return CacheManager(enabled=True, default_ttl=60)


def test_cache_basic_operations(cache_manager):
    """Test basic cache operations (get, set, invalidate)."""
    # Set a value
    cache_manager.set("test_cache", "test_key", "test_value")

    # Get the value
    value = cache_manager.get("test_cache", "test_key")
    assert value == "test_value"

    # Invalidate the value
    cache_manager.invalidate("test_cache", "test_key")

    # Verify the value is gone
    value = cache_manager.get("test_cache", "test_key")
    assert value is None


def test_cache_ttl(cache_manager):
    """Test cache TTL functionality."""
    # Set a value with a short TTL
    cache_manager.set("test_cache", "ttl_key", "ttl_value", ttl=1)

    # Verify the value is there
    value = cache_manager.get("test_cache", "ttl_key")
    assert value == "ttl_value"

    # Wait for the TTL to expire
    time.sleep(1.1)

    # Verify the value is gone
    value = cache_manager.get("test_cache", "ttl_key")
    assert value is None


def test_cache_enable_disable(cache_manager):
    """Test enabling and disabling the cache."""
    # Set a value
    cache_manager.set("test_cache", "enable_key", "enable_value")

    # Verify the value is there
    value = cache_manager.get("test_cache", "enable_key")
    assert value == "enable_value"

    # Disable the cache
    cache_manager.disable()

    # Verify the cache is disabled
    assert cache_manager.enabled is False

    # Verify the value is not returned when cache is disabled
    value = cache_manager.get("test_cache", "enable_key")
    assert value is None

    # Enable the cache
    cache_manager.enable()

    # Verify the cache is enabled
    assert cache_manager.enabled is True

    # Verify the value is returned again
    value = cache_manager.get("test_cache", "enable_key")
    assert value == "enable_value"


def test_cache_clear(cache_manager):
    """Test clearing the cache."""
    # Set multiple values
    cache_manager.set("test_cache1", "key1", "value1")
    cache_manager.set("test_cache1", "key2", "value2")
    cache_manager.set("test_cache2", "key1", "value3")

    # Verify the values are there
    assert cache_manager.get("test_cache1", "key1") == "value1"
    assert cache_manager.get("test_cache1", "key2") == "value2"
    assert cache_manager.get("test_cache2", "key1") == "value3"

    # Clear one cache
    cache_manager.clear("test_cache1")

    # Verify test_cache1 is empty but test_cache2 still has values
    assert cache_manager.get("test_cache1", "key1") is None
    assert cache_manager.get("test_cache1", "key2") is None
    assert cache_manager.get("test_cache2", "key1") == "value3"

    # Clear all caches
    cache_manager.clear()

    # Verify all caches are empty
    assert cache_manager.get("test_cache2", "key1") is None


def test_cache_stats(cache_manager):
    """Test cache statistics."""
    # Set a value
    cache_manager.set("test_cache", "stats_key", "stats_value")

    # Get the value a few times
    for _ in range(3):
        value = cache_manager.get("test_cache", "stats_key")
        assert value == "stats_value"

    # Try to get a non-existent value
    for _ in range(2):
        value = cache_manager.get("test_cache", "nonexistent_key")
        assert value is None

    # Get the stats
    stats = cache_manager.stats

    # Verify the stats have the expected structure
    assert "hit_count" in stats
    assert "miss_count" in stats
    assert "hit_rate" in stats
    assert "cache_count" in stats
    assert "entry_counts" in stats

    # Verify the stats have the expected values
    assert stats["hit_count"] == 3
    assert stats["miss_count"] == 2
    assert stats["hit_rate"] == 3 / 5
    assert stats["cache_count"] == 1
    assert "test_cache" in stats["entry_counts"]
    assert stats["entry_counts"]["test_cache"] == 1


def test_cache_size(cache_manager):
    """Test getting cache size."""
    # Set multiple values
    cache_manager.set("test_cache1", "key1", "value1")
    cache_manager.set("test_cache1", "key2", "value2")
    cache_manager.set("test_cache2", "key1", "value3")

    # Get the size of a specific cache
    size1 = cache_manager.get_cache_size("test_cache1")
    assert size1 == 2

    # Get the size of another specific cache
    size2 = cache_manager.get_cache_size("test_cache2")
    assert size2 == 1

    # Get the total size of all caches
    total_size = cache_manager.get_cache_size()
    assert total_size == 3


def test_client_cache_integration(client):
    """Test that the client correctly integrates with the cache manager."""
    # Verify the client has a cache manager
    assert hasattr(client, "cache")
    assert client.cache is not None

    # Verify the cache is enabled by default
    assert client.cache.enabled is True

    # Disable the cache
    client.cache.disable()

    # Verify the cache is disabled
    assert client.cache.enabled is False

    # Enable the cache
    client.cache.enable()

    # Verify the cache is enabled
    assert client.cache.enabled is True

    # Clear the cache
    client.clear_cache()

    # Verify the cache stats are reset
    assert client.cache.stats["hit_count"] == 0
    assert client.cache.stats["miss_count"] == 0


def test_cached_decorator(cache_manager):
    """Test the cached decorator."""

    # Define a function with the cached decorator
    @cache_manager.cached("test_cache")
    def test_function(arg):
        # This would normally be an expensive operation
        return f"processed_{arg}"

    # Call the function twice with the same argument
    result1 = test_function("test")
    result2 = test_function("test")

    # Verify both calls return the same result
    assert result1 == "processed_test"
    assert result2 == "processed_test"

    # Verify the cache was hit on the second call
    assert cache_manager.stats["hit_count"] == 1
    assert cache_manager.stats["miss_count"] == 1


def test_cache_with_team_manager(client):
    """Test that the TeamManager correctly uses the cache."""
    # Clear the cache first
    client.clear_cache()

    # Get the test team name
    import os
    test_team_name = os.getenv("LINEAR_TEST_TEAM", "Test")

    # Get the team ID by name (this should miss the cache)
    team_id = client.teams.get_id_by_name(test_team_name)

    # Verify the cache missed
    assert client.cache.stats["miss_count"] >= 1

    # Get the team ID by name again (this should hit the cache)
    team_id_again = client.teams.get_id_by_name(test_team_name)

    # Verify the cache hit
    assert client.cache.stats["hit_count"] >= 1

    # Verify both calls return the same ID
    assert team_id == team_id_again
