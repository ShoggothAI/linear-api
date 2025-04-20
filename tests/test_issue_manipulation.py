import pytest
import time

from linear_api.issue_manipulation import (
    create_issue,
    set_parent_issue,
    get_linear_issue,
    delete_issue,
    update_issue,
)
from linear_api.domain import LinearIssueInput, LinearIssueUpdateInput, LinearPriority
from linear_api.get_resources import get_states, team_name_to_id
from linear_api.project_manipulation import create_project, delete_project


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"


@pytest.fixture
def test_issue_input(test_team_name):
    """Fixture to create a test issue input."""
    return LinearIssueInput(
        title="Test Issue from Unit Test",
        teamName=test_team_name,
        description="This is a test issue created by a unit test",
        priority=LinearPriority.MEDIUM,
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

    # Clean up the issue
    issue_id = response["issueCreate"]["issue"]["id"]
    delete_issue(issue_id)


def test_create_issue_with_different_priority(test_team_name):
    """Test creating an issue with a different priority."""
    # Create a test issue with high priority
    high_priority_issue = LinearIssueInput(
        title="High Priority Test Issue",
        teamName=test_team_name,
        description="This is a high priority test issue",
        priority=LinearPriority.URGENT,  # Urgent priority
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

    # Clean up the issue
    issue_id = response["issueCreate"]["issue"]["id"]
    delete_issue(issue_id)


def test_create_issue_with_state_and_project(test_team_name):
    """Test creating an issue with state and project names."""
    # Get the first available state for the team

    team_id = team_name_to_id(test_team_name)
    states = get_states(team_id)

    # Skip test if no states are available
    if not states:
        pytest.skip("No states available for testing")

    # Create a test project
    project_name = f"Test Project {int(time.time())}"
    project_response = create_project(
        name=project_name,
        team_name=test_team_name,
        description="Test project for issue creation"
    )
    project_id = project_response["projectCreate"]["project"]["id"]

    state_name = next(iter(states.keys()))

    # Create a test issue with state and project
    issue = LinearIssueInput(
        title="Issue with State and Project",
        teamName=test_team_name,
        description="This issue has a specific state and project",
        stateName=state_name,
        projectName=project_name,
        priority=LinearPriority.MEDIUM,
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

    # Clean up - delete the issue and project
    issue_id = response["issueCreate"]["issue"]["id"]
    delete_issue(issue_id)
    delete_project(project_id)


def test_create_issue_with_invalid_team():
    """Test creating an issue with an invalid team name."""
    # Create a test issue with an invalid team name
    invalid_issue = LinearIssueInput(
        title="Invalid Team Issue",
        teamName="invalid_team_name",  # This name doesn't exist
        description="This issue has an invalid team",
        priority=LinearPriority.MEDIUM,
    )

    # The API should return an error when trying to create the issue
    # This should raise a ValueError specifically
    with pytest.raises(ValueError):
        create_issue(invalid_issue)


def test_create_issue_with_invalid_state(test_team_name):
    """Test creating an issue with an invalid state name."""
    # Create a test issue with an invalid state name
    invalid_issue = LinearIssueInput(
        title="Invalid State Issue",
        teamName=test_team_name,
        stateName="invalid_state_name",  # This name doesn't exist
        description="This issue has an invalid state",
        priority=LinearPriority.MEDIUM,
    )

    # This should raise a ValueError specifically
    with pytest.raises(ValueError):
        create_issue(invalid_issue)


def test_create_issue_with_invalid_project(test_team_name):
    """Test creating an issue with an invalid project name."""
    # Create a test issue with an invalid project name
    invalid_issue = LinearIssueInput(
        title="Invalid Project Issue",
        teamName=test_team_name,
        projectName="invalid_project_name",  # This name doesn't exist
        description="This issue has an invalid project",
        priority=LinearPriority.MEDIUM,
    )

    # This should raise a ValueError specifically
    with pytest.raises(ValueError):
        create_issue(invalid_issue)


def test_set_parent_issue(test_team_name):
    """Test setting a parent-child relationship between issues."""
    # Create a parent issue
    parent_issue_input = LinearIssueInput(
        title="Parent Issue",
        teamName=test_team_name,
        description="This is a parent issue",
        priority=LinearPriority.MEDIUM,
    )

    # Create a child issue
    child_issue_input = LinearIssueInput(
        title="Child Issue",
        teamName=test_team_name,
        description="This is a child issue",
        priority=LinearPriority.MEDIUM,
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

    # Clean up the issues
    delete_issue(child_id)
    delete_issue(parent_id)


def test_create_issue_with_parent(test_team_name):
    """Test creating an issue with a parent relationship in one step."""
    # First create a parent issue
    parent_issue_input = LinearIssueInput(
        title="Parent for One-Step Test",
        teamName=test_team_name,
        description="This is a parent issue for testing one-step creation",
        priority=LinearPriority.MEDIUM,
    )

    parent_response = create_issue(parent_issue_input)
    parent_id = parent_response["issueCreate"]["issue"]["id"]

    # Now create a child issue with parentId set
    child_issue_input = LinearIssueInput(
        title="Child with One-Step Creation",
        teamName=test_team_name,
        description="This child issue should be linked to its parent in one step",
        priority=LinearPriority.MEDIUM,
        parentId=parent_id,
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

    # Clean up the issues
    child_id = response["issueCreate"]["issue"]["id"]
    delete_issue(child_id)
    delete_issue(parent_id)


def test_create_issue_with_metadata(test_team_name):
    """Test creating an issue with metadata and verifying it can be retrieved."""
    # Create a test issue with metadata
    metadata = {
        "foo": "bar",
    }
    issue_input = LinearIssueInput(
        title="Issue with Metadata",
        teamName=test_team_name,
        description="This issue has metadata attached",
        priority=LinearPriority.MEDIUM,
        metadata=metadata,
    )

    # Create the issue
    response = create_issue(issue_input)

    # Verify the response has the expected structure
    assert "issueCreate" in response
    assert "issue" in response["issueCreate"]
    assert "id" in response["issueCreate"]["issue"]

    # Get the issue ID
    issue_id = response["issueCreate"]["issue"]["id"]

    # Retrieve the issue to check its metadata
    retrieved_issue = get_linear_issue(issue_id)

    # Verify the metadata property contains our key-value pair
    assert retrieved_issue.metadata is not None
    assert "foo" in retrieved_issue.metadata
    assert retrieved_issue.metadata["foo"] == "bar"

    # Clean up the issue
    delete_issue(issue_id)


def test_update_issue(test_team_name):
    """Test updating an existing issue."""
    # First create an issue to update
    issue_input = LinearIssueInput(
        title="Issue to Update",
        teamName=test_team_name,
        description="This issue will be updated",
        priority=LinearPriority.MEDIUM,
    )

    # Create the issue
    response = create_issue(issue_input)
    issue_id = response["issueCreate"]["issue"]["id"]

    # Update the issue with new values
    update_data = LinearIssueUpdateInput(
        title="Updated Issue Title",
        description="This issue has been updated",
        priority=LinearPriority.HIGH,
    )

    # Call the update function
    update_response = update_issue(issue_id, update_data)

    # Verify the response has the expected structure
    assert "issueUpdate" in update_response
    assert "success" in update_response["issueUpdate"]
    assert update_response["issueUpdate"]["success"] is True
    assert "issue" in update_response["issueUpdate"]

    # Verify the updated values
    updated_issue = update_response["issueUpdate"]["issue"]
    assert updated_issue["title"] == update_data.title
    assert updated_issue["description"] == update_data.description
    assert updated_issue["priority"] == update_data.priority.value

    # Retrieve the issue to double-check the updates
    retrieved_issue = get_linear_issue(issue_id)
    assert retrieved_issue.title == update_data.title
    assert retrieved_issue.description == update_data.description
    assert retrieved_issue.priority == update_data.priority

    # Clean up the issue
    delete_issue(issue_id)


def test_update_issue_with_state_and_project(test_team_name):
    """Test updating an issue with state and project names."""
    # Get the first available state for the team

    team_id = team_name_to_id(test_team_name)
    states = get_states(team_id)

    # Skip test if no states are available
    if not states:
        pytest.skip("No states available for testing")

    # Get two different states if possible
    state_names = list(states.keys())

    if len(state_names) < 2:
        pytest.skip("Need at least two states for this test")

    # Create two test projects
    project1_name = f"Test Project 1 {int(time.time())}"
    project1_response = create_project(
        name=project1_name,
        team_name=test_team_name,
        description="First test project for issue update"
    )
    project1_id = project1_response["projectCreate"]["project"]["id"]

    project2_name = f"Test Project 2 {int(time.time())}"
    project2_response = create_project(
        name=project2_name,
        team_name=test_team_name,
        description="Second test project for issue update"
    )
    project2_id = project2_response["projectCreate"]["project"]["id"]

    # Create an issue with the first state and project
    issue_input = LinearIssueInput(
        title="Issue with State and Project to Update",
        teamName=test_team_name,
        stateName=state_names[0],
        projectName=project1_name,
    )

    # Create the issue
    response = create_issue(issue_input)
    issue_id = response["issueCreate"]["issue"]["id"]

    # Update the issue with the second state and project
    update_data = LinearIssueUpdateInput(
        stateName=state_names[1],
        projectName=project2_name,
    )

    # Call the update function
    update_response = update_issue(issue_id, update_data)

    # Verify the response has the expected structure
    assert "issueUpdate" in update_response
    assert "success" in update_response["issueUpdate"]
    assert update_response["issueUpdate"]["success"] is True

    # Retrieve the issue to check the updates
    retrieved_issue = get_linear_issue(issue_id)

    # Verify the state and project were updated
    assert retrieved_issue.state.name == state_names[1]
    assert retrieved_issue.project.name == project2_name

    # Clean up the issue and projects
    delete_issue(issue_id)
    delete_project(project1_id)
    delete_project(project2_id)
