"""
Base resource manager for Linear API.

This module provides the BaseManager class that all resource managers inherit from.
"""

from typing import Dict, Any, Optional, TypeVar, Generic, List, Type, Callable, Union, cast

from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)
V = TypeVar('V')


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
        result = self._execute_raw_query(query, variables or {})
        return result

    def enable_connection_unwrapping(self) -> None:
        """Enable automatic connection unwrapping."""
        self._auto_unwrap_connections = True

    def disable_connection_unwrapping(self) -> None:
        """Disable automatic connection unwrapping."""
        self._auto_unwrap_connections = False

    def _handle_pagination(
            self,
            query: str,
            variables: Dict[str, Any],
            node_path: List[str],
            model_class: Optional[Type[V]] = None,
            transform_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
            initial_cursor: Optional[str] = None
    ) -> List[V]:
        """
        Handle pagination for GraphQL queries that return collections.

        Args:
            query: The GraphQL query string with cursor parameter
            variables: Variables for the query (without cursor)
            node_path: Path to the nodes in the response (e.g., ["issues", "nodes"])
            model_class: Optional Pydantic model class to convert results to
            transform_func: Optional function to transform each item before conversion
            initial_cursor: Optional starting cursor

        Returns:
            List of resources, optionally converted to model_class instances
        """
        results = []
        cursor = initial_cursor
        max_retries = 3  # Constant value for retries

        while True:
            retry_count = 0
            success = False

            while not success and retry_count <= max_retries:
                try:
                    # Add cursor to variables if we have one
                    query_vars = {**variables}
                    if cursor:
                        query_vars["cursor"] = cursor

                    # Execute the query
                    response = self._execute_raw_query(query, query_vars)
                    success = True  # Query succeeded

                except Exception as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        # Log error and exit pagination loop
                        import logging
                        logging.error(f"Failed to execute query after {max_retries} attempts: {e}")
                        return results  # Return what we've collected so far

                    # Exponential backoff before retrying
                    import time
                    wait_time = 2 ** retry_count
                    time.sleep(wait_time)

            if not success:
                break  # If it failed after all attempts - exit

            # Navigate through result to extract nodes
            nodes_container = response
            page_info = None

            try:
                # Navigate to the nodes container
                for path_segment in node_path[:-1]:
                    if path_segment not in nodes_container:
                        break
                    nodes_container = nodes_container[path_segment]

                # Save reference to pageInfo for checking next page
                if "pageInfo" in nodes_container:
                    page_info = nodes_container["pageInfo"]

                # Extract nodes
                nodes = []
                if node_path[-1] in nodes_container:
                    nodes = nodes_container[node_path[-1]]

                # Process each node
                for node in nodes:
                    if transform_func:
                        node = transform_func(node)

                    if model_class:
                        try:
                            # Convert to model instance
                            node = model_class(**node)
                        except Exception as e:
                            import logging
                            logging.warning(f"Error converting node to {model_class.__name__}: {e}")
                            # Continue with raw node if conversion fails

                    results.append(node)

            except Exception as e:
                import logging
                logging.warning(f"Error processing query results: {e}")
                # Continue with what we were able to process

            # Check if there are more pages
            has_next_page = False
            if page_info and "hasNextPage" in page_info:
                has_next_page = page_info.get("hasNextPage", False)

            if has_next_page and "endCursor" in page_info and page_info["endCursor"]:
                cursor = page_info["endCursor"]
            else:
                break  # No more pages or no valid cursor

        # If model_class is specified, ensure all items are of that type
        if model_class is not None:
            # Convert any remaining dict items to models
            for i, item in enumerate(results):
                if isinstance(item, dict) and not isinstance(item, model_class):
                    try:
                        results[i] = model_class(**item)
                    except Exception as e:
                        import logging
                        logging.warning(f"Error converting item to {model_class.__name__}: {e}")

        return results

    def _extract_nodes(
            self,
            response: Dict[str, Any],
            node_path: List[str],
            model_class: Optional[Type[V]] = None
    ) -> List[V]:
        """
        Extract nodes from a nested response without pagination.
        Useful for getting a list directly from a single response.

        Args:
            response: The API response dictionary
            node_path: Path to the nodes in the response
            model_class: Optional model class to convert items

        Returns:
            List of extracted nodes, optionally converted to model instances
        """
        # Navigate to the containing object
        container = response
        for segment in node_path[:-1]:
            if segment not in container:
                return []
            container = container[segment]

        # Get the nodes array
        final_segment = node_path[-1]
        if final_segment not in container:
            return []

        nodes = container[final_segment]

        # Convert to model instances if needed
        if model_class is not None:
            converted_nodes = []
            for node in nodes:
                if isinstance(node, dict) and not isinstance(node, model_class):
                    try:
                        converted_nodes.append(model_class(**node))
                    except Exception as e:
                        print(f"Error converting to {model_class.__name__}: {e}")
                        converted_nodes.append(node)  # Use original node on error
                else:
                    converted_nodes.append(node)
            return converted_nodes

        return nodes

    def _handle_connection_response(
            self,
            response: Dict[str, Any],
            connection_path: List[str],
            model_class: Optional[Type[V]] = None
    ) -> List[V]:
        """
        Process a response containing a GraphQL connection and return the nodes directly.

        Args:
            response: The API response dictionary
            connection_path: Path to the connection in the response
            model_class: Optional model class to convert items

        Returns:
            List of nodes extracted from the connection
        """
        # Build the full path to nodes
        node_path = connection_path + ["nodes"]
        return self._extract_nodes(response, node_path, model_class)

    def _extract_and_cache(
            self,
            response: Dict[str, Any],
            connection_path: List[str],
            cache_name: str,
            cache_key: Any,
            model_class: Optional[Type[V]] = None
    ) -> List[V]:
        """
        Extract nodes from a connection response, cache them, and return them as a list.

        This is a convenience method that combines extraction and caching in one step.

        Args:
            response: The API response
            connection_path: Path to the connection
            cache_name: Name of the cache to use
            cache_key: Key for caching the result
            model_class: Optional model class for conversion

        Returns:
            List of extracted nodes
        """
        # Extract the nodes
        nodes = self._handle_connection_response(response, connection_path, model_class)

        # Cache the result
        if nodes:
            self._cache_set(cache_name, cache_key, nodes)

        return nodes

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
        cached_value = self.client.cache.get(full_cache_name, key)

        # Handle compatibility with old Connection objects
        if cached_value is not None and hasattr(cached_value, 'nodes'):
            return cached_value.nodes

        return cached_value

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
