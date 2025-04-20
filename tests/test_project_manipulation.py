import pytest
import time
from linear_api.project_manipulation import create_project, delete_project, get_project
from linear_api.domain import LinearProject
from linear_api.get_resources import team_name_to_id, get_projects


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"


@pytest.fixture
def test_project(test_team_name):
    """Create a test project and clean up after the test."""
    # Create a unique project name using timestamp to avoid conflicts
    project_name = f"Test Project {int(time.time())}"

    # Create the project
    response = create_project(
        name=project_name,
        team_name=test_team_name,
        description="This is a test project created by automated tests"
    )

    # Extract the project ID
    project_id = response["projectCreate"]["project"]["id"]

    # Return the project ID and name for use in tests
    project_data = {"id": project_id, "name": project_name}

    # Yield the project data for the test to use
    yield project_data

    # Clean up after the test by deleting the project
    try:
        delete_project(project_id)
    except ValueError:
        # Project might have already been deleted in the test
        pass


def test_create_project(test_team_name):
    """Test creating a project."""
    # Create a unique project name
    project_name = f"Test Create Project {int(time.time())}"

    # Create the project
    response = create_project(
        name=project_name,
        team_name=test_team_name,
        description="This is a test project for testing project creation"
    )

    # Verify the response has the expected structure
    assert "projectCreate" in response
    assert "success" in response["projectCreate"]
    assert response["projectCreate"]["success"] is True
    assert "project" in response["projectCreate"]
    assert "id" in response["projectCreate"]["project"]
    assert "name" in response["projectCreate"]["project"]

    # Verify the name matches what we sent
    assert response["projectCreate"]["project"]["name"] == project_name

    # Clean up - delete the project
    project_id = response["projectCreate"]["project"]["id"]
    delete_project(project_id)


def test_get_project(test_project):
    """Test getting a project by ID."""
    # Get the project
    project = get_project(test_project["id"])

    # Verify the project is a LinearProject instance
    assert isinstance(project, LinearProject)

    # Verify the project has the expected properties
    assert project.id == test_project["id"]
    assert project.name == test_project["name"]
    assert project.description is not None


def test_delete_project(test_team_name):
    """Test deleting a project."""
    # First create a project to delete
    project_name = f"Test Delete Project {int(time.time())}"

    # Create the project
    response = create_project(
        name=project_name,
        team_name=test_team_name
    )

    # Get the project ID
    project_id = response["projectCreate"]["project"]["id"]

    # Delete the project
    delete_response = delete_project(project_id)

    # Verify the response has the expected structure
    assert "projectDelete" in delete_response
    assert "success" in delete_response["projectDelete"]
    assert delete_response["projectDelete"]["success"] is True

    # Verify the project no longer exists by checking if it's in the list of projects
    # First, get the team ID
    team_id = team_name_to_id(test_team_name)

    # Get all projects for the team
    projects = get_projects(team_id)

    # Check that our deleted project is not in the list
    project_ids = list(projects.values())
    assert project_id not in project_ids


def test_create_project_with_invalid_team():
    """Test creating a project with an invalid team name."""
    # Try to create a project with a non-existent team
    with pytest.raises(ValueError):
        create_project(
            name="Invalid Team Project",
            team_name="NonExistentTeam"
        )


def test_delete_nonexistent_project():
    """Test deleting a non-existent project."""
    # Try to delete a project with a non-existent ID
    with pytest.raises(ValueError):
        delete_project("non-existent-project-id")
