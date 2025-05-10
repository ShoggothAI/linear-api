"""
Tests for pagination functionality in the Linear API client.

This module tests the pagination implementation, error handling,
and performance with large datasets.
"""

import time
from unittest.mock import patch

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

    # Create and return the client
    return LinearClient(api_key=api_key)


def test_handle_pagination_basic(client):
    """Test the basic functionality of the pagination handler."""
    # Create a simple query that returns paginated results
    query = """
    query($cursor: String) {
        teams(first: 2, after: $cursor) {
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

    # Use the pagination handler to get all teams
    teams = client.teams._handle_pagination(
        query,
        {},
        ["teams", "nodes"]
    )

    # Verify we got a list of team data
    assert isinstance(teams, list)
    assert len(teams) > 0

    # Verify each team has the expected fields
    for team in teams:
        assert "id" in team
        assert "name" in team


def test_handle_pagination_with_model_conversion(client):
    """Test that pagination can convert results to model instances."""
    from linear_api.domain import LinearTeam

    # Create a query that returns teams
    query = """
    query($cursor: String) {
        teams(first: 2, after: $cursor) {
            nodes {
                id
                name
                key
                description
                color
                icon
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Use the pagination handler with model conversion
    teams = client.teams._handle_pagination(
        query,
        {},
        ["teams", "nodes"],
        LinearTeam  # Pass the model class for automatic conversion
    )

    # Verify we got a list of LinearTeam instances
    assert isinstance(teams, list)
    assert len(teams) > 0
    assert all(isinstance(team, LinearTeam) for team in teams)

    # Verify each team has the expected properties
    for team in teams:
        assert team.id is not None
        assert team.name is not None
        assert hasattr(team, 'key')


def test_handle_pagination_with_transform(client):
    """Test pagination with a transform function."""
    # Create a query that returns issues
    query = """
    query($cursor: String) {
        issues(first: 2, after: $cursor) {
            nodes {
                id
                title
                number
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Define a transform function
    def transform_func(issue):
        issue["transformed"] = True
        issue["title_with_number"] = f"#{issue['number']} - {issue['title']}"
        return issue

    # Use the pagination handler with the transform function
    issues = client.issues._handle_pagination(
        query,
        {},
        ["issues", "nodes"],
        transform_func=transform_func
    )

    # Verify we got a list of transformed issue data
    assert isinstance(issues, list)
    assert len(issues) > 0

    # Verify each issue was transformed
    for issue in issues:
        assert "transformed" in issue
        assert issue["transformed"] is True
        assert "title_with_number" in issue
        assert issue["title_with_number"] == f"#{issue['number']} - {issue['title']}"


@pytest.mark.parametrize("model_class,node_path", [
    (None, ["teams", "nodes"]),  # No model conversion
    ("LinearTeam", ["teams", "nodes"]),  # With model conversion
])
def test_pagination_with_retries(client, model_class, node_path):
    """Test that pagination properly retries failed requests."""
    from linear_api.domain import LinearTeam

    # Create a simple query
    query = """
    query($cursor: String) {
        teams(first: 2, after: $cursor) {
            nodes {
                id
                name
                key
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Mock _execute_raw_query to fail on first call, succeed on second
    original_execute = client.teams._execute_raw_query
    call_count = [0]  # Use a list to hold the call count for nonlocal modification

    def mock_execute(query, variables):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call fails
            raise Exception("Simulated network error")
        # Subsequent calls succeed
        return original_execute(query, variables)

    # Use the real LinearTeam class if specified
    actual_model_class = LinearTeam if model_class == "LinearTeam" else model_class

    # Apply the mock
    with patch.object(client.teams, '_execute_raw_query', side_effect=mock_execute):
        # Execute pagination with retry logic
        results = client.teams._handle_pagination(
            query,
            {},
            node_path,
            model_class=actual_model_class
        )

    # Verify we got results despite the first call failing
    assert len(results) > 0

    # Check that the results are of the right type
    if model_class == "LinearTeam":
        assert isinstance(results[0], LinearTeam)
    else:
        assert isinstance(results[0], dict)
        assert "id" in results[0]
        assert "name" in results[0]


def test_pagination_with_multiple_failures(client):
    """Test pagination behavior with multiple consecutive failures."""
    # Create a simple query
    query = """
    query($cursor: String) {
        teams(first: 2, after: $cursor) {
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

    # Mock _execute_raw_query to fail multiple times, then succeed
    original_execute = client.teams._execute_raw_query
    call_count = [0]

    def mock_execute(query, variables):
        call_count[0] += 1
        if call_count[0] <= 3:  # Fail for the first 3 calls
            raise Exception(f"Simulated network error #{call_count[0]}")
        # Subsequent calls succeed
        return original_execute(query, variables)

    # Apply the mock
    with patch.object(client.teams, '_execute_raw_query', side_effect=mock_execute):
        # Execute pagination with retry logic
        results = client.teams._handle_pagination(
            query,
            {},
            ["teams", "nodes"]
        )

    # Verify we got results despite multiple failures
    assert len(results) > 0
    assert "id" in results[0]
    assert "name" in results[0]


def test_pagination_with_too_many_failures(client):
    """Test that pagination stops after too many consecutive failures."""
    # Create a simple query
    query = """
    query($cursor: String) {
        teams(first: 2, after: $cursor) {
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

    # Mock _execute_raw_query to always fail
    def mock_execute(query, variables):
        raise Exception("Simulated persistent network error")

    # Capture log messages
    with patch.object(client.teams, '_execute_raw_query', side_effect=mock_execute):
        with patch('logging.error') as mock_log:
            # Execute pagination with retry logic
            results = client.teams._handle_pagination(
                query,
                {},
                ["teams", "nodes"]
            )

    # Verify that pagination returned an empty list after failing
    assert isinstance(results, list)
    assert len(results) == 0

    # Verify that an error was logged
    mock_log.assert_called()


def test_pagination_with_partial_failures(client):
    """Test pagination when some pages succeed and others fail."""
    # Get the team ID
    import os
    test_team_name = os.getenv("LINEAR_TEST_TEAM", "Test")
    team_id = client.teams.get_id_by_name(test_team_name)

    # Create a query that will return multiple pages
    query = """
    query($teamId: String!, $cursor: String) {
        team(id: $teamId) {
            issues(first: 5, after: $cursor) {
                nodes {
                    id
                    title
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """

    # Mock _execute_raw_query to succeed for the first page, fail for the second, succeed for the third
    original_execute = client.issues._execute_raw_query
    call_count = [0]

    def mock_execute(query, variables):
        call_count[0] += 1
        if call_count[0] == 2:  # Fail only on the second page
            raise Exception("Simulated network error on second page")
        # Other calls succeed
        return original_execute(query, variables)

    # Apply the mock
    with patch.object(client.issues, '_execute_raw_query', side_effect=mock_execute):
        # Execute pagination with retry logic
        results = client.issues._handle_pagination(
            query,
            {"teamId": team_id},
            ["team", "issues", "nodes"]
        )

    # Verify we got at least some results from the first and third pages
    assert len(results) > 0

    # We expect the results to include items from the first and third pages
    # (or more if there are more pages), but not the second page which failed
    # and was presumably skipped or retried
    for issue in results:
        assert "id" in issue
        assert "title" in issue


def test_pagination_with_missing_node_path(client):
    """Test pagination behavior when the node path is invalid."""
    # Create a query
    query = """
    query($cursor: String) {
        teams(first: 2, after: $cursor) {
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

    # Use an invalid node path
    results = client.teams._handle_pagination(
        query,
        {},
        ["invalid", "path", "nodes"]
    )

    # Verify we got an empty list since the path doesn't exist
    assert isinstance(results, list)
    assert len(results) == 0


def test_pagination_with_malformed_response(client):
    """Test pagination behavior when the response is malformed."""
    # Create a simple query
    query = """
    query($cursor: String) {
        teams(first: 2, after: $cursor) {
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

    # Mock _execute_raw_query to return a malformed response
    def mock_execute(query, variables):
        # Return a response with missing pageInfo
        return {"teams": {"nodes": [{"id": "123", "name": "Test Team"}]}}

    # Apply the mock
    with patch.object(client.teams, '_execute_raw_query', side_effect=mock_execute):
        # Execute pagination with retry logic
        results = client.teams._handle_pagination(
            query,
            {},
            ["teams", "nodes"]
        )

    # Verify we got at least the results from the first response
    assert len(results) == 1
    assert results[0]["id"] == "123"
    assert results[0]["name"] == "Test Team"


def test_performance_with_large_dataset(client):
    """Test the performance of pagination with a larger dataset."""
    # Get the team ID of a team with many issues
    import os
    test_team_name = os.getenv("LINEAR_TEST_TEAM", "Development")  # Using Development which has more issues

    try:
        team_id = client.teams.get_id_by_name(test_team_name)
    except ValueError:
        pytest.skip(f"Team '{test_team_name}' not found, skipping test")

    # Query to get all issues for this team
    query = """
    query($teamId: String!, $cursor: String) {
        team(id: $teamId) {
            issues(first: 20, after: $cursor) {
                nodes {
                    id
                    title
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
    """

    # Measure time to retrieve all issues
    start_time = time.time()
    issues = client.issues._handle_pagination(
        query,
        {"teamId": team_id},
        ["team", "issues", "nodes"]
    )
    end_time = time.time()

    # Log the results
    print(f"Retrieved {len(issues)} issues in {end_time - start_time:.2f} seconds")

    # Verify we got a reasonable number of results
    assert len(issues) > 0

    # No strict performance assertion, but we can log for manual review
    if len(issues) > 50:
        print(
            f"Large dataset test: {len(issues)} issues processed at {len(issues) / (end_time - start_time):.1f} issues/second")


def test_pagination_nested_connections(client):
    """Test pagination with nested connections."""
    # Get the team ID
    import os
    test_team_name = os.getenv("LINEAR_TEST_TEAM", "Test")
    team_id = client.teams.get_id_by_name(test_team_name)

    # Create a query with nested connections
    query = """
    query($teamId: String!, $cursor: String) {
        team(id: $teamId) {
            projects(first: 2, after: $cursor) {
                nodes {
                    id
                    name
                    issues {
                        nodes {
                            id
                            title
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

    # Get projects with pagination
    projects = client.projects._handle_pagination(
        query,
        {"teamId": team_id},
        ["team", "projects", "nodes"]
    )

    # Verify we got projects
    assert isinstance(projects, list)

    # If we have projects, verify they have nested issues
    if projects:
        for project in projects:
            assert "id" in project
            assert "name" in project
            assert "issues" in project
            assert "nodes" in project["issues"]


def test_pagination_with_model_inheritance(client):
    """Test pagination with model inheritance and polymorphic types."""
    # Define a query with hierarchical/polymorphic types
    query = """
    query($cursor: String) {
        issues(first: 5, after: $cursor) {
            nodes {
                id
                title
                creator {
                    ... on User {
                        id
                        name
                        email
                    }
                }
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Get issues with pagination
    issues = client.issues._handle_pagination(
        query,
        {},
        ["issues", "nodes"]
    )

    # Verify we got issues
    assert isinstance(issues, list)
    assert len(issues) > 0

    # Verify each issue has creator data if available
    for issue in issues:
        if "creator" in issue and issue["creator"]:
            assert "id" in issue["creator"]
            assert "name" in issue["creator"]


def test_multi_level_pagination_handling(client):
    """Test how pagination is handled when multiple levels need pagination."""
    # Create a query with multiple levels that could require pagination
    query = """
    query($cursor1: String) {
        teams(first: 2, after: $cursor1) {
            nodes {
                id
                name
                projects(first: 2) {  # Inner pagination - this would normally need cursor handling
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
    """

    # Use pagination handler
    teams = client.teams._handle_pagination(
        query,
        {},
        ["teams", "nodes"]
    )

    # Verify we got teams
    assert isinstance(teams, list)
    assert len(teams) > 0

    # Verify each team has projects (but only the first page of projects)
    for team in teams:
        assert "id" in team
        assert "name" in team
        assert "projects" in team
        assert "nodes" in team["projects"]
