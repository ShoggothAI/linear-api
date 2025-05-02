"""
Base resource manager for Linear API.

This module provides the BaseManager class that all resource managers inherit from.
"""

from typing import Dict, Any, Optional, TypeVar, Generic, List, Type
from pydantic import BaseModel

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

    def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query with variables.

        Args:
            query: The GraphQL query string
            variables: Optional variables for the query

        Returns:
            The API response data
        """
        return self.client.execute_graphql(query, variables)

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
            response = self._execute_query(query, query_vars)

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
