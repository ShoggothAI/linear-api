"""
Connection unwrapper for Linear API.

This module provides utility functions for automatically unwrapping GraphQL connections
in API responses, handling pagination transparently.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Callable
import copy
import logging

logger = logging.getLogger(__name__)


class ConnectionUnwrapper:
    """
    Helper class for unwrapping GraphQL connections automatically.

    This class provides methods to detect and unwrap GraphQL connection patterns
    in API responses, handling pagination seamlessly.
    """

    def __init__(self, query_executor: Callable):
        """
        Initialize the unwrapper with a query executor function.

        Args:
            query_executor: A callable that executes GraphQL queries
        """
        self.execute_query = query_executor
        self.max_depth = 5  # Maximum recursion depth for pagination
        self.processed_paths = set()  # Track processed paths to prevent infinite loops

    def unwrap_connections(self, data: Any, query: str, variables: Dict[str, Any]) -> Any:
        """
        Recursively unwrap all connection patterns in the response.

        Args:
            data: The GraphQL response data
            query: The original GraphQL query string
            variables: The variables used in the query

        Returns:
            The modified data with unwrapped connections
        """
        if not isinstance(data, dict):
            return data

        # Make a deep copy to avoid modifying the original data during processing
        result = copy.deepcopy(data)

        # Process all connections in the response
        self._process_connections(result, [], query, variables)

        return result

    def _process_connections(self, data: Any, path: List[str], query: str,
                             variables: Dict[str, Any], depth: int = 0) -> None:
        """
        Recursively process all connections in the data.

        Args:
            data: The data to process
            path: The current path in the data structure
            query: The original GraphQL query
            variables: The variables used in the query
            depth: Current recursion depth
        """
        if depth > self.max_depth:
            logger.warning(f"Max recursion depth reached at path {'.'.join(path)}")
            return

        if not isinstance(data, dict):
            return

        # Check if current object is a connection
        is_connection = self._is_connection(data)

        # Process this node if it's a connection
        if is_connection:
            path_str = '.'.join(path)
            if path_str in self.processed_paths:
                return

            self.processed_paths.add(path_str)
            self._unwrap_connection(data, path, query, variables, depth)

        # Continue recursively processing children
        for key, value in list(data.items()):
            if isinstance(value, dict):
                self._process_connections(value, path + [key], query, variables, depth + 1)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._process_connections(item, path + [key, str(i)], query, variables, depth + 1)

    def _is_connection(self, data: Dict[str, Any]) -> bool:
        """
        Check if a dictionary represents a GraphQL connection.

        Args:
            data: The dictionary to check

        Returns:
            True if the dictionary is a connection, False otherwise
        """
        return (
                isinstance(data, dict) and
                "nodes" in data and
                isinstance(data["nodes"], list) and
                "pageInfo" in data and
                isinstance(data["pageInfo"], dict) and
                "hasNextPage" in data["pageInfo"] and
                "endCursor" in data["pageInfo"]
        )

    def _extract_path_from_query(self, path: List[str], query: str) -> Optional[str]:
        """
        Attempt to extract the corresponding path in the GraphQL query.
        This is a heuristic approach and may not work for all queries.

        Args:
            path: The path in the response
            query: The GraphQL query

        Returns:
            A string representing the path in the query, or None if not found
        """
        # This is a simplified implementation that might need enhancement
        # based on the specific GraphQL schema and query complexity
        return None

    def _construct_pagination_query(self, query: str, path: List[str],
                                    cursor: str) -> Optional[str]:
        """
        Attempt to construct a pagination query for the specified path.

        Args:
            query: The original query
            path: The path to the connection
            cursor: The cursor for pagination

        Returns:
            A modified query for fetching the next page, or None if not possible
        """
        # This is a placeholder for a more sophisticated implementation
        # that would parse and modify the GraphQL query
        return None

    def _unwrap_connection(self, data: Dict[str, Any], path: List[str],
                           query: str, variables: Dict[str, Any], depth: int) -> None:
        """
        Unwrap a connection by fetching all pages and combining them.

        Args:
            data: The connection data to unwrap
            path: The path to the connection
            query: The original query
            variables: The query variables
            depth: Current recursion depth
        """
        all_nodes = list(data["nodes"])
        page_info = data["pageInfo"]

        # If no next page, nothing to do
        if not page_info.get("hasNextPage", False):
            return

        cursor = page_info.get("endCursor")
        if not cursor:
            return

        # Prepare variables for pagination
        pagination_vars = copy.deepcopy(variables)

        # Add the cursor to the variables
        # This assumes that the query has a cursor parameter with the
        # appropriate name for the path we're processing

        # We need to guess the cursor parameter name
        # Strategy 1: Use the last path component + "Cursor"
        if path:
            cursor_param = f"{path[-1]}Cursor"
            pagination_vars[cursor_param] = cursor

        # Strategy 2: Just use "cursor" or "after"
        pagination_vars["cursor"] = cursor
        pagination_vars["after"] = cursor

        # Try executing the query with the cursor
        try:
            next_page = self.execute_query(query, pagination_vars)

            # Navigate to the same path in the response
            current = next_page
            for p in path:
                if p.isdigit():  # Handle array indices
                    idx = int(p)
                    if isinstance(current, list) and idx < len(current):
                        current = current[idx]
                    else:
                        return  # Path doesn't exist in pagination response
                elif p in current:
                    current = current[p]
                else:
                    return  # Path doesn't exist in pagination response

            # Check if we've reached a valid connection
            if not self._is_connection(current):
                return

            # Add nodes from the next page
            all_nodes.extend(current["nodes"])

            # If there are more pages, recursively process them
            if current["pageInfo"].get("hasNextPage", False):
                # Update the connection data with what we have so far
                data["nodes"] = all_nodes
                data["pageInfo"] = current["pageInfo"]

                # Recursively process the next page
                self._unwrap_connection(data, path, query, pagination_vars, depth + 1)
            else:
                # This was the last page, update the connection data
                data["nodes"] = all_nodes
                data["pageInfo"]["hasNextPage"] = False
                data["pageInfo"]["endCursor"] = current["pageInfo"].get("endCursor")

        except Exception as e:
            logger.warning(f"Error unwrapping connection at {'.'.join(path)}: {e}")
