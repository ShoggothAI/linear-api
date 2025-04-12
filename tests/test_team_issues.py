import pytest

from linear_api.issue_manipulation import create_issue, get_team_issues, delete_issue
from linear_api.domain import LinearIssueInput, LinearPriority


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"  # Replace with an actual team name if needed


@pytest.fixture
def test_issue(test_team_name):
    """Create a test issue to use for tests."""
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
    return {"id": issue_id, "title": issue_title}


def test_get_team_issues(test_team_name, test_issue):
    """Test getting all issues for a team."""
    # Get all issues for the team
    issues = get_team_issues(test_team_name)
    
    # Verify that the response is a dictionary
    assert isinstance(issues, dict)
    
    # Verify that our test issue is in the response
    assert test_issue["id"] in issues
    assert issues[test_issue["id"]] == test_issue["title"]


def test_get_team_issues_invalid_team():
    """Test getting issues for a non-existent team."""
    # This should raise a ValueError
    with pytest.raises(ValueError):
        get_team_issues("NonExistentTeam")


def test_delete_issue(test_issue):
    """Test deleting an issue."""
    # Delete the test issue
    response = delete_issue(test_issue["id"])
    
    # Verify the response has the expected structure
    assert "issueDelete" in response
    assert "success" in response["issueDelete"]
    assert response["issueDelete"]["success"] is True
    
    # Verify that the issue is no longer in the team's issues
    # This assumes the test is running with a valid team name
    team_name = "Test"  # Same as in the fixture
    issues = get_team_issues(team_name)
    assert test_issue["id"] not in issues


def test_delete_nonexistent_issue():
    """Test deleting a non-existent issue."""
    # This should raise a ValueError
    with pytest.raises(ValueError):
        delete_issue("non-existent-issue-id")
