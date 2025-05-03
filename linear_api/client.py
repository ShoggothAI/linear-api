"""
Linear API Client

A well-organized client for interacting with the Linear API.
This module provides the main entry point for the Linear API library.
"""

import os
from typing import Optional, Dict, Any

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

        # Get an issue
        issue = client.issues.get("issue-id")

        # Create a project
        project = client.projects.create(
            name="New Project",
            team_name="Engineering"
        )
        ```
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Linear API client.

        Args:
            api_key: The Linear API key. If not provided, the LINEAR_API_KEY
                    environment variable will be used.

        Raises:
            ValueError: If no API key is provided and LINEAR_API_KEY environment
                       variable is not set.
        """
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Either pass api_key parameter or set LINEAR_API_KEY environment variable."
            )

        # Initialize resource managers
        self.issues = IssueManager(self)
        self.projects = ProjectManager(self)
        self.teams = TeamManager(self)
        self.users = UserManager(self)

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

    def validate_schema(
        self, model_class: type, graphql_type_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate the domain models against the GraphQL schema.

        Returns:
            A dictionary mapping model names to validation results
        """
        return validate_model(model_class, graphql_type_name, api_key=self.api_key)
