import pytest
from linearpy.issue_manipulation import create_issue, set_parent_issue
from linearpy.domain import Issue, Team
from linearpy.get_teams import team_name_to_id


@pytest.fixture
def test_team():
    """Fixture to create a test team."""
    team_name = "Test"
    team_id = team_name_to_id(team_name)
    return Team(id=team_id, name=team_name)


@pytest.fixture
def test_issue(test_team):
    """Fixture to create a test issue."""
    return Issue(
        id="",
        title="Test Issue from Unit Test",
        team=test_team,
        description="This is a test issue created by a unit test",
        priority=2
    )


def test_create_issue(test_issue):
    """Test creating an issue with the Linear API."""
    # Call the function
    response = create_issue(test_issue)

    # Verify the response has the expected structure
    assert "issueCreate" in response
    assert "issue" in response["issueCreate"]
    assert "id" in response["issueCreate"]["issue"]
    assert "title" in response["issueCreate"]["issue"]

    # Verify the title matches what we sent
    assert response["issueCreate"]["issue"]["title"] == test_issue.title


def test_create_issue_with_different_priority(test_team):
    """Test creating an issue with a different priority."""
    # Create a test issue with high priority
    high_priority_issue = Issue(
        id="",
        title="High Priority Test Issue",
        team=test_team,
        description="This is a high priority test issue",
        priority=4  # High priority
    )

    # Call the function
    response = create_issue(high_priority_issue)

    # Verify the response has the expected structure
    assert "issueCreate" in response
    assert "issue" in response["issueCreate"]
    assert "id" in response["issueCreate"]["issue"]
    assert "title" in response["issueCreate"]["issue"]

    # Verify the title matches what we sent
    assert response["issueCreate"]["issue"]["title"] == high_priority_issue.title


def test_create_issue_with_invalid_team():
    """Test creating an issue with an invalid team name."""
    # Create a team with an invalid name
    invalid_team = Team(id="", name="NonExistentTeam")

    # Create a test issue with the invalid team
    invalid_issue = Issue(
        id="",
        title="Invalid Team Issue",
        team=invalid_team,
        description="This issue has an invalid team",
        priority=2
    )

    # Expect a ValueError when trying to create the issue
    with pytest.raises(ValueError, match="Team NonExistentTeam not found"):
        create_issue(invalid_issue)


def test_set_parent_issue(test_team):
    """Test setting a parent-child relationship between issues."""
    # Create a parent issue
    parent_issue = Issue(
        id="",
        title="Parent Issue",
        team=test_team,
        description="This is a parent issue",
        priority=2
    )

    # Create a child issue
    child_issue = Issue(
        id="",
        title="Child Issue",
        team=test_team,
        description="This is a child issue",
        priority=3
    )

    # Create both issues in Linear
    parent_response = create_issue(parent_issue)
    child_response = create_issue(child_issue)

    # Update the issue objects with the actual IDs
    parent_issue.id = parent_response["issueCreate"]["issue"]["id"]
    child_issue.id = child_response["issueCreate"]["issue"]["id"]

    # Set the parent-child relationship
    response = set_parent_issue(child_issue, parent_issue)

    # Verify the response has the expected structure
    assert "issueUpdate" in response
    assert "issue" in response["issueUpdate"]
    assert "parent" in response["issueUpdate"]["issue"]
    assert "id" in response["issueUpdate"]["issue"]["parent"]

    # Verify the parent ID matches what we set
    assert response["issueUpdate"]["issue"]["parent"]["id"] == parent_issue.id
