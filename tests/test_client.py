"""
Tests for the LinearClient class.

This module tests the core functionality of the LinearClient class.
"""

import pytest
import os
from linear_api import LinearClient


@pytest.fixture
def client():
    """Create a LinearClient instance for testing."""
    # Get the API key from environment variable
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        pytest.skip("LINEAR_API_KEY environment variable not set")

    # Create and return the client
    return LinearClient(api_key=api_key)


def test_client_initialization():
    """Test that the client can be initialized with an API key."""
    # Get the API key from environment variable
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        pytest.skip("LINEAR_API_KEY environment variable not set")

    # Create the client with explicit API key
    client = LinearClient(api_key=api_key)

    # Verify the client was created
    assert client is not None
    assert client.api_key == api_key


def test_client_initialization_from_env():
    """Test that the client can be initialized from the environment variable."""
    # Get the API key from environment variable
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        pytest.skip("LINEAR_API_KEY environment variable not set")

    # Create the client without explicit API key
    client = LinearClient()

    # Verify the client was created
    assert client is not None
    assert client.api_key == api_key


def test_client_initialization_failure():
    """Test that the client raises an error when no API key is provided."""
    # Temporarily clear the environment variable
    original_api_key = os.environ.pop("LINEAR_API_KEY", None)

    try:
        # Attempt to create the client without an API key
        with pytest.raises(ValueError):
            LinearClient()
    finally:
        # Restore the environment variable
        if original_api_key:
            os.environ["LINEAR_API_KEY"] = original_api_key


def test_client_resource_managers(client):
    """Test that the client has all the required resource managers."""
    # Verify all resource managers are available
    assert client.issues is not None
    assert client.projects is not None
    assert client.teams is not None
    assert client.users is not None


def test_client_api_call(client):
    """Test that the client can make API calls."""
    # Simple query to get the current user
    query = """
    query {
        viewer {
            id
            name
            email
        }
    }
    """

    # Call the API
    response = client.call_api({"query": query})

    # Verify the response has the expected structure
    assert response is not None
    assert "viewer" in response
    assert "id" in response["viewer"]
    assert "name" in response["viewer"]
    assert "email" in response["viewer"]


def test_client_execute_graphql(client):
    """Test that the client can execute GraphQL queries with variables."""
    # Query to get a specific team
    query = """
    query GetTeams {
        teams {
            nodes {
                id
                name
            }
        }
    }
    """

    # Execute the query
    response = client.execute_graphql(query)

    # Verify the response has the expected structure
    assert response is not None
    assert "teams" in response
    assert "nodes" in response["teams"]
