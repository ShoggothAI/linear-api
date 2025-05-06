"""
Linear API Client

A well-organized client for interacting with the Linear API.
This module provides the main entry point for the Linear API library.
"""

import os
from typing import Optional, Dict, Any

from .domain.base_domain import LinearModel

from .managers.cache_manager import CacheManager
from .managers.issue_manager import IssueManager
from .managers.project_manager import ProjectManager
from .managers.team_manager import TeamManager
from .managers.user_manager import UserManager
from .schema_validator import validate_model
from .utils.api import call_linear_api


class LinearClient:
    """
    Main client for the Linear API.

    This class provides a unified interface to all Linear API resources
    and serves as the entry point for the library.

    Example:
        ```python
        # Create a client with an API key
        client = LinearClient(api_key="your_api_key")

        # Or use environment variable
        client = LinearClient()  # Uses LINEAR_API_KEY environment variable

        # Disable caching if needed
        client.cache.disable()

        # Disable connection unwrapping if needed
        client.disable_connection_unwrapping()

        # Get an issue
        issue = client.issues.get("issue-id")

        # Create a project
        project = client.projects.create(
            name="New Project",
            team_name="Engineering"
        )
        ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        auto_unwrap_connections: bool = True,
    ):
        """
        Initialize the Linear API client.

        Args:
            api_key: The Linear API key. If not provided, the LINEAR_API_KEY
                    environment variable will be used.
            enable_cache: Whether to enable caching (default: True)
            cache_ttl: Default time-to-live for cached items in seconds (default: 1 hour)
            auto_unwrap_connections: Whether to automatically unwrap GraphQL connections (default: True)

        Raises:
            ValueError: If no API key is provided and LINEAR_API_KEY environment
                       variable is not set.
        """
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Either pass api_key parameter or set LINEAR_API_KEY environment variable."
            )

        # Initialize cache manager
        self.cache = CacheManager(enabled=enable_cache, default_ttl=cache_ttl)

        # Initialize resource managers
        self.issues = IssueManager(self)
        self.projects = ProjectManager(self)
        self.teams = TeamManager(self)
        self.users = UserManager(self)

        # Configure connection unwrapping based on initial setting
        if not auto_unwrap_connections:
            self.disable_connection_unwrapping()

    def call_api(self, query: Dict[str, Any] | str) -> Dict[str, Any]:
        """
        Call the Linear API with the provided query.

        Args:
            query: The GraphQL query or mutation to execute

        Returns:
            The API response data

        Raises:
            ValueError: If the API call fails
        """
        return call_linear_api(query, api_key=self.api_key)

    def execute_graphql(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query with variables.

        Args:
            query: The GraphQL query string
            variables: Optional variables for the query

        Returns:
            The API response data
        """
        request = {"query": query}
        if variables:
            request["variables"] = variables

        return self.call_api(request)

    def validate_schema(self, model_class: type[LinearModel]) -> Dict[str, Dict[str, Any]]:
        """
        Validate the domain models against the GraphQL schema.

        Returns:
            A dictionary mapping model names to validation results
        """
        return validate_model(model_class, api_key=self.api_key)

    def clear_cache(self, cache_name: Optional[str] = None) -> None:
        """
        Clear cache data.

        Args:
            cache_name: Optional name of specific cache to clear. If None, clears all caches.
        """
        self.cache.clear(cache_name)

    def enable_connection_unwrapping(self) -> None:
        """
        Enable automatic unwrapping of GraphQL connections in all managers.

        This settings improves usability by automatically handling pagination,
        but may increase the number of API calls for large data sets.
        """
        self.issues.enable_connection_unwrapping()
        self.projects.enable_connection_unwrapping()
        self.teams.enable_connection_unwrapping()
        self.users.enable_connection_unwrapping()

    def disable_connection_unwrapping(self) -> None:
        """
        Disable automatic unwrapping of GraphQL connections in all managers.

        This setting reduces the number of API calls but requires manual
        handling of pagination for large data sets.
        """
        self.issues.disable_connection_unwrapping()
        self.projects.disable_connection_unwrapping()
        self.teams.disable_connection_unwrapping()
        self.users.disable_connection_unwrapping()
