import pytest
from datetime import datetime
from linearpy.issue_manipulation import create_issue, set_parent_issue, get_linear_issue
from linearpy.domain import Issue, Team, LinearIssueCreateInput, LinearPriority
from linearpy.get_resources import team_name_to_id, get_teams


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"


@pytest.fixture
def test_issue_input(test_team_name):
    """Fixture to create a test issue input."""
    return LinearIssueCreateInput(
        title="Test Issue from Unit Test",
        teamName=test_team_name,
        description="This is a test issue created by a unit test",
        priority=LinearPriority.MEDIUM
    )


def test_create_issue(test_issue_input):
    """Test creating an issue with the Linear API."""
    # Call the function
    response = create_issue(test_issue_input)

    # Verify the response has the expected structure
    assert "issueCreate" in response
    assert "issue" in response["issueCreate"]
    assert "id" in response["issueCreate"]["issue"]
    assert "title" in response["issueCreate"]["issue"]

    # Verify the title matches what we sent
    assert response["issueCreate"]["issue"]["title"] == test_issue_input.title


def test_create_issue_with_different_priority(test_team_name):
    """Test creating an issue with a different priority."""
    # Create a test issue with high priority
    high_priority_issue = LinearIssueCreateInput(
        title="High Priority Test Issue",
        teamName=test_team_name,
        description="This is a high priority test issue",
        priority=LinearPriority.URGENT  # Urgent priority
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


def test_create_issue_with_state_and_project(test_team_name):
    """Test creating an issue with state and project names."""
    # Get the first available state and project for the team
    from linearpy.get_resources import get_states, get_projects, team_name_to_id

    team_id = team_name_to_id(test_team_name)
    states = get_states(team_id)
    projects = get_projects(team_id)

    # Skip test if no states or projects are available
    if not states or not projects:
        pytest.skip("No states or projects available for testing")

    state_name = next(iter(states.keys()))
    project_name = next(iter(projects.keys()))

    # Create a test issue with state and project
    issue = LinearIssueCreateInput(
        title="Issue with State and Project",
        teamName=test_team_name,
        description="This issue has a specific state and project",
        stateName=state_name,
        projectName=project_name,
        priority=LinearPriority.MEDIUM
    )

    # Call the function
    response = create_issue(issue)

    # Verify the response has the expected structure
    assert "issueCreate" in response
    assert "issue" in response["issueCreate"]
    assert "id" in response["issueCreate"]["issue"]
    assert "title" in response["issueCreate"]["issue"]

    # Verify the title matches what we sent
    assert response["issueCreate"]["issue"]["title"] == issue.title


def test_create_issue_with_invalid_team():
    """Test creating an issue with an invalid team name."""
    # Create a test issue with an invalid team name
    invalid_issue = LinearIssueCreateInput(
        title="Invalid Team Issue",
        teamName="invalid_team_name",  # This name doesn't exist
        description="This issue has an invalid team",
        priority=LinearPriority.MEDIUM
    )

    # The API should return an error when trying to create the issue
    # This should raise a ValueError specifically
    with pytest.raises(ValueError):
        create_issue(invalid_issue)


def test_create_issue_with_invalid_state(test_team_name):
    """Test creating an issue with an invalid state name."""
    # Create a test issue with an invalid state name
    invalid_issue = LinearIssueCreateInput(
        title="Invalid State Issue",
        teamName=test_team_name,
        stateName="invalid_state_name",  # This name doesn't exist
        description="This issue has an invalid state",
        priority=LinearPriority.MEDIUM
    )

    # This should raise a ValueError specifically
    with pytest.raises(ValueError):
        create_issue(invalid_issue)


def test_create_issue_with_invalid_project(test_team_name):
    """Test creating an issue with an invalid project name."""
    # Create a test issue with an invalid project name
    invalid_issue = LinearIssueCreateInput(
        title="Invalid Project Issue",
        teamName=test_team_name,
        projectName="invalid_project_name",  # This name doesn't exist
        description="This issue has an invalid project",
        priority=LinearPriority.MEDIUM
    )

    # This should raise a ValueError specifically
    with pytest.raises(ValueError):
        create_issue(invalid_issue)


def test_set_parent_issue(test_team_name):
    """Test setting a parent-child relationship between issues."""
    # Create a parent issue
    parent_issue_input = LinearIssueCreateInput(
        title="Parent Issue",
        teamName=test_team_name,
        description="This is a parent issue",
        priority=LinearPriority.MEDIUM
    )

    # Create a child issue
    child_issue_input = LinearIssueCreateInput(
        title="Child Issue",
        teamName=test_team_name,
        description="This is a child issue",
        priority=LinearPriority.MEDIUM
    )

    # Create both issues in Linear
    parent_response = create_issue(parent_issue_input)
    child_response = create_issue(child_issue_input)

    # Extract the IDs from the responses
    parent_id = parent_response["issueCreate"]["issue"]["id"]
    child_id = child_response["issueCreate"]["issue"]["id"]

    # Set the parent-child relationship
    response = set_parent_issue(child_id, parent_id)

    # Verify the response has the expected structure
    assert "issueUpdate" in response
    assert "issue" in response["issueUpdate"]
    assert "parent" in response["issueUpdate"]["issue"]
    assert "id" in response["issueUpdate"]["issue"]["parent"]

    # Verify the parent ID matches what we set
    assert response["issueUpdate"]["issue"]["parent"]["id"] == parent_id


def test_create_issue_with_parent(test_team_name):
    """Test creating an issue with a parent relationship in one step."""
    # First create a parent issue
    parent_issue_input = LinearIssueCreateInput(
        title="Parent for One-Step Test",
        teamName=test_team_name,
        description="This is a parent issue for testing one-step creation",
        priority=LinearPriority.MEDIUM
    )

    parent_response = create_issue(parent_issue_input)
    parent_id = parent_response["issueCreate"]["issue"]["id"]

    # Now create a child issue with parentId set
    child_issue_input = LinearIssueCreateInput(
        title="Child with One-Step Creation",
        teamName=test_team_name,
        description="This child issue should be linked to its parent in one step",
        priority=LinearPriority.MEDIUM,
        parentId=parent_id
    )

    # Create the child issue with parent relationship
    response = create_issue(child_issue_input)

    # Verify the response has the expected structure
    assert "issueCreate" in response
    assert "issue" in response["issueCreate"]
    assert "id" in response["issueCreate"]["issue"]

    # Verify that the parentRelationship was set
    assert "parentRelationship" in response
    assert "issueUpdate" in response["parentRelationship"]
    assert "issue" in response["parentRelationship"]["issueUpdate"]
    assert "parent" in response["parentRelationship"]["issueUpdate"]["issue"]
    assert "id" in response["parentRelationship"]["issueUpdate"]["issue"]["parent"]

    # Verify the parent ID matches what we set
    assert response["parentRelationship"]["issueUpdate"]["issue"]["parent"]["id"] == parent_id
