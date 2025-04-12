import pytest

from linear_api.issue_manipulation import create_issue, get_team_issues, delete_issue
from linear_api.domain import LinearIssueInput, LinearPriority


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"  # Replace with an actual team name if needed


@pytest.fixture
def test_issue(test_team_name):
    """Create a test issue to use for tests and clean up after the test."""
    # Create a new issue
    issue_input = LinearIssueInput(
        title="Test Issue for Team Issues Tests",
        teamName=test_team_name,
        description="This is a test issue for testing team issues functions",
        priority=LinearPriority.MEDIUM
    )

    response = create_issue(issue_input)
    issue_id = response["issueCreate"]["issue"]["id"]
    issue_title = response["issueCreate"]["issue"]["title"]

    # Return the issue ID and title for use in tests
    issue_data = {"id": issue_id, "title": issue_title}

    # Yield the issue data for the test to use
    yield issue_data

    # Clean up after the test by deleting the issue
    try:
        delete_issue(issue_id)
    except ValueError:
        # Issue might have already been deleted in the test
        pass


@pytest.fixture
def get_issues_test_issue(test_team_name):
    """Create a test issue specifically for the get_team_issues test."""
    # Create a new issue
    issue_input = LinearIssueInput(
        title="Test Issue for get_team_issues Test",
        teamName=test_team_name,
        description="This is a test issue for testing the get_team_issues function",
        priority=LinearPriority.MEDIUM
    )

    response = create_issue(issue_input)
    issue_id = response["issueCreate"]["issue"]["id"]
    issue_title = response["issueCreate"]["issue"]["title"]

    # Return the issue data
    issue_data = {"id": issue_id, "title": issue_title}

    # Yield the issue data for the test to use
    yield issue_data

    # Clean up after the test
    try:
        delete_issue(issue_id)
    except ValueError:
        pass


def test_get_team_issues(test_team_name, get_issues_test_issue):
    """Test getting all issues for a team."""
    # Get all issues for the team
    issues = get_team_issues(test_team_name)

    # Verify that the response is a dictionary
    assert isinstance(issues, dict)

    # Verify that our test issue is in the response
    assert get_issues_test_issue["id"] in issues
    assert issues[get_issues_test_issue["id"]] == get_issues_test_issue["title"]


def test_get_team_issues_invalid_team():
    """Test getting issues for a non-existent team."""
    # This should raise a ValueError
    with pytest.raises(ValueError):
        get_team_issues("NonExistentTeam")


def test_delete_issue(test_team_name, test_issue):
    """Test deleting an issue."""
    # Delete the test issue
    response = delete_issue(test_issue["id"])

    # Verify the response has the expected structure
    assert "issueDelete" in response
    assert "success" in response["issueDelete"]
    assert response["issueDelete"]["success"] is True

    # Verify that the issue is no longer in the team's issues
    issues = get_team_issues(test_team_name)
    assert test_issue["id"] not in issues

    # Note: The fixture will try to delete this issue again in cleanup,
    # but it will catch the ValueError since we've already deleted it


def test_delete_nonexistent_issue():
    """Test deleting a non-existent issue."""
    # This should raise a ValueError
    with pytest.raises(ValueError):
        delete_issue("non-existent-issue-id")
