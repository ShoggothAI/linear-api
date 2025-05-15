"""
Tests for the ConnectionUnwrapper class.

This module tests the functionality of automatic GraphQL connection unwrapping.
"""

import pytest
from linear_api import LinearClient


@pytest.fixture
def client():
    """Create a LinearClient instance for testing."""
    # Get the API key from environment variable
    import os
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        pytest.skip("LINEAR_API_KEY environment variable not set")

    # Create and return the client with connection unwrapping enabled
    return LinearClient(api_key=api_key, auto_unwrap_connections=True)


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"  # Using the test team


def test_connection_unwrapper_initialization(client):
    """Test that connection unwrapper is correctly initialized in the client."""
    # Verify BaseManager classes have connection unwrapping enabled
    assert hasattr(client.teams, "_auto_unwrap_connections")
    assert client.teams._auto_unwrap_connections is True


def test_connection_unwrapping_enable_disable(client):
    """Test enabling and disabling connection unwrapping."""
    # Verify connection unwrapping is enabled by default
    assert client.teams._auto_unwrap_connections is True

    # Disable connection unwrapping
    client.disable_connection_unwrapping()

    # Verify connection unwrapping is disabled
    assert client.teams._auto_unwrap_connections is False
    assert client.issues._auto_unwrap_connections is False
    assert client.projects._auto_unwrap_connections is False
    assert client.users._auto_unwrap_connections is False

    # Enable connection unwrapping
    client.enable_connection_unwrapping()

    # Verify connection unwrapping is enabled
    assert client.teams._auto_unwrap_connections is True
    assert client.issues._auto_unwrap_connections is True
    assert client.projects._auto_unwrap_connections is True
    assert client.users._auto_unwrap_connections is True


def test_connection_unwrapping_simple_query(client):
    """Test connection unwrapping with a simple query."""
    # Create a query with a simple connection pattern
    query = """
    query {
        teams {
            nodes {
                id
                name
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Execute the query with unwrapping enabled
    result = client.teams._execute_query(query)

    # Verify the result has the expected structure
    assert "teams" in result
    assert "nodes" in result["teams"]
    assert isinstance(result["teams"]["nodes"], list)

    # Verify there are teams in the result
    assert len(result["teams"]["nodes"]) > 0

    # Verify each team has the expected structure
    for team in result["teams"]["nodes"]:
        assert "id" in team
        assert "name" in team


def test_connection_unwrapping_nested_query(client, test_team_name):
    """Test connection unwrapping with a nested query."""
    # Get the team ID for the test team
    team_id = client.teams.get_id_by_name(test_team_name)

    # Create a query with nested connection patterns
    query = """
    query($teamId: String!) {
        team(id: $teamId) {
            id
            name
            issues(first: 10) {
                nodes {
                    id
                    title
                    labels {
                        nodes {
                            id
                            name
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """

    # Execute the query with unwrapping enabled
    result = client.teams._execute_query(query, {"teamId": team_id})

    # Verify the result has the expected structure
    assert "team" in result
    assert "id" in result["team"]
    assert "name" in result["team"]
    assert "issues" in result["team"]
    assert "nodes" in result["team"]["issues"]

    # Verify the team is the one we requested
    assert result["team"]["id"] == team_id
    assert result["team"]["name"] == test_team_name

    # Verify there are issues in the result (might be empty if the team has no issues)
    # Each issue might have its own labels connection
    issues = result["team"]["issues"]["nodes"]
    for issue in issues:
        assert "id" in issue
        assert "title" in issue
        assert "labels" in issue
        assert "nodes" in issue["labels"]


def test_connection_unwrapping_comparison(client):
    """Compare results with connection unwrapping enabled and disabled."""
    # Create a query with a simple connection pattern
    query = """
    query {
        teams(first: 5) {
            nodes {
                id
                name
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Execute the query with unwrapping enabled
    result_unwrapped = client.teams._execute_query(query)

    # Disable unwrapping
    client.disable_connection_unwrapping()

    # Execute the query with unwrapping disabled
    result_wrapped = client.teams._execute_raw_query(query)

    # Re-enable unwrapping
    client.enable_connection_unwrapping()

    # If there's only one page, the results might be identical
    # But if there are multiple pages, the unwrapped result should have more items

    # Verify both results have teams
    assert "teams" in result_unwrapped
    assert "nodes" in result_unwrapped["teams"]
    assert "teams" in result_wrapped
    assert "nodes" in result_wrapped["teams"]

    # Check if there are more pages
    has_more_pages = result_wrapped["teams"]["pageInfo"]["hasNextPage"]

    if has_more_pages:
        # If there are more pages, the unwrapped result should have more items
        assert len(result_unwrapped["teams"]["nodes"]) > len(result_wrapped["teams"]["nodes"])
    else:
        # If there's only one page, the results should have the same number of items
        assert len(result_unwrapped["teams"]["nodes"]) == len(result_wrapped["teams"]["nodes"])


def test_connection_unwrapping_with_manual_pagination(client):
    """Test that manual pagination still works when unwrapping is disabled."""
    # Disable connection unwrapping
    client.disable_connection_unwrapping()

    # Create a query for manual pagination
    query = """
    query GetTeams($cursor: String) {
        teams(first: 10, after: $cursor) {
            nodes {
                id
                name
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Use manual pagination
    teams = client.teams._handle_pagination(
        query,
        {},
        ["teams", "nodes"]
    )

    # Verify the result has teams
    assert len(teams) > 0

    # Re-enable connection unwrapping
    client.enable_connection_unwrapping()


def test_connection_unwrapping_real_world(client):
    """Test connection unwrapping with a real-world scenario: getting all issues for a team."""
    # Get the test team name
    import os
    test_team_name = os.getenv("LINEAR_TEST_TEAM", "Test")

    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Create a query to get all issues for the team
    query = """
    query($teamId: String!) {
        team(id: $teamId) {
            issues {
                nodes {
                    id
                    title
                    state {
                        id
                        name
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """

    # Execute the query with unwrapping enabled
    result = client.teams._execute_query(query, {"teamId": team_id})

    # Verify the result has the team and its issues
    assert "team" in result
    assert "issues" in result["team"]
    assert "nodes" in result["team"]["issues"]

    # Compare with the get_by_team method
    issues_from_method = client.issues.get_by_team(test_team_name)

    # The method might do additional processing, so just check that we have issues
    assert len(result["team"]["issues"]["nodes"]) > 0
    assert len(issues_from_method) > 0
