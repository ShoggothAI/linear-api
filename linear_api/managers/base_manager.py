"""
Base resource manager for Linear API.

This module provides the BaseManager class that all resource managers inherit from.
"""

from typing import Dict, Any, Optional, TypeVar, Generic, List, Type, Callable

from pydantic import BaseModel

from ..utils.connection_unwrapper import ConnectionUnwrapper

T = TypeVar('T', bound=BaseModel)


class BaseManager(Generic[T]):
    """
    Base class for all resource managers.

    This class provides common functionality for all resource managers.
    Each resource manager is responsible for a specific type of resource
    (e.g., issues, projects, teams).
    """

    def __init__(self, client):
        """
        Initialize the manager with a client reference.

        Args:
            client: The LinearClient instance this manager belongs to
        """
        self.client = client
        self._resource_type_name = self.__class__.__name__.replace("Manager", "")
        self._connection_unwrapper = ConnectionUnwrapper(self._execute_raw_query)
        self._auto_unwrap_connections = True  # Flag to control automatic unwrapping

    def _execute_raw_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query with variables without any post-processing.

        Args:
            query: The GraphQL query string
            variables: Optional variables for the query

        Returns:
            The raw API response data
        """
        return self.client.execute_graphql(query, variables)

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query with variables.

        If auto_unwrap_connections is enabled, this method automatically
        unwraps all connection patterns in the response, handling pagination
        transparently.

        Args:
            query: The GraphQL query string
            variables: Optional variables for the query

        Returns:
            The API response data with unwrapped connections if enabled
        """
        result = self._execute_raw_query(query, variables)

        # Apply connection unwrapping if enabled
        if self._auto_unwrap_connections:
            return self._connection_unwrapper.unwrap_connections(result, query, variables or {})

        return result

    def enable_connection_unwrapping(self) -> None:
        """Enable automatic connection unwrapping."""
        self._auto_unwrap_connections = True

    def disable_connection_unwrapping(self) -> None:
        """Disable automatic connection unwrapping."""
        self._auto_unwrap_connections = False

    def _cache_get(self, cache_name: str, key: Any) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            cache_name: The cache name
            key: The cache key

        Returns:
            The cached value or None if not found
        """
        # Prefix cache name with resource type for better organization
        full_cache_name = f"{self._resource_type_name}_{cache_name}"
        return self.client.cache.get(full_cache_name, key)

    def _cache_set(self, cache_name: str, key: Any, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.

        Args:
            cache_name: The cache name
            key: The cache key
            value: The value to cache
            ttl: Optional time-to-live in seconds
        """
        # Prefix cache name with resource type for better organization
        full_cache_name = f"{self._resource_type_name}_{cache_name}"
        self.client.cache.set(full_cache_name, key, value, ttl)

    def _cache_clear(self, cache_name: Optional[str] = None) -> None:
        """
        Clear a cache or all caches for this resource type.

        Args:
            cache_name: The cache name to clear, or None to clear all caches for this resource type
        """
        if cache_name is None:
            # Clear all caches for this resource type
            for cache in self.client.cache._caches.keys():
                if cache.startswith(f"{self._resource_type_name}_"):
                    self.client.cache.clear(cache)
        else:
            full_cache_name = f"{self._resource_type_name}_{cache_name}"
            self.client.cache.clear(full_cache_name)

    def _cache_invalidate(self, cache_name: str, key: Any) -> None:
        """
        Invalidate a specific cache entry.

        Args:
            cache_name: The cache name
            key: The key to invalidate
        """
        full_cache_name = f"{self._resource_type_name}_{cache_name}"
        self.client.cache.invalidate(full_cache_name, key)

    def _cached(self, cache_name: str,
                key_fn: Callable = lambda *args, **kwargs: str(args) + str(kwargs)):
        """
        Decorator for caching function results.

        Args:
            cache_name: The cache name
            key_fn: Function to generate cache key from arguments

        Returns:
            Decorated function
        """
        full_cache_name = f"{self._resource_type_name}_{cache_name}"
        return self.client.cache.cached(full_cache_name, key_fn)

    def _handle_pagination(
            self,
            query: str,
            variables: Dict[str, Any],
            node_path: List[str],
            model_class: Type[T] = None,
            transform_func=None
    ) -> List[T]:
        """
        Handle pagination for GraphQL queries that return collections.

        Note: This method is maintained for backward compatibility.
        For new code, automatic connection unwrapping is recommended instead.

        Args:
            query: The GraphQL query string with cursor parameter
            variables: Variables for the query (without cursor)
            node_path: Path to the nodes in the response (e.g., ["issues", "nodes"])
            model_class: Optional Pydantic model class to convert results to
            transform_func: Optional function to transform each item before conversion

        Returns:
            List of resources, optionally converted to model_class instances
        """
        results = []
        cursor = None

        while True:
            # Add cursor to variables if we have one
            query_vars = {**variables}
            if cursor:
                query_vars["cursor"] = cursor

            # Execute the query
            response = self._execute_raw_query(query, query_vars)

            # Navigate to the nodes using the node_path
            nodes_container = response
            for path_segment in node_path[:-1]:
                if path_segment not in nodes_container:
                    break
                nodes_container = nodes_container[path_segment]

            # Extract the nodes
            if node_path[-1] in nodes_container:
                nodes = nodes_container[node_path[-1]]

                # Process each node
                for node in nodes:
                    if transform_func:
                        node = transform_func(node)

                    if model_class:
                        node = model_class(**node)

                    results.append(node)

            # Check if there are more pages
            if (
                    "pageInfo" in nodes_container
                    and nodes_container["pageInfo"].get("hasNextPage", False)
            ):
                cursor = nodes_container["pageInfo"]["endCursor"]
            else:
                break

        return results
