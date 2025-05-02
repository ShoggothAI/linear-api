"""
Tests for the ProjectManager class.

This module tests the functionality of the ProjectManager class.
"""

import pytest
import time
import uuid

from linear_api import LinearClient
from linear_api.domain import LinearProject


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


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"  # Using the test team


@pytest.fixture
def test_project(client, test_team_name):
    """Create a test project and clean up after the test."""
    # Create a unique project name using timestamp to avoid conflicts
    project_name = f"Test Project {int(time.time())}"

    # Create the project
    project = client.projects.create(
        name=project_name,
        team_name=test_team_name,
        description="This is a test project created by automated tests"
    )

    # Return the project for use in tests
    yield project

    # Clean up after the test by deleting the project
    try:
        client.projects.delete(project.id)
    except ValueError:
        # Project might have already been deleted in the test
        pass


def test_get_project(client, test_project):
    """Test getting a project by ID."""
    # Get the project
    project = client.projects.get(test_project.id)

    # Verify the project is a LinearProject instance
    assert isinstance(project, LinearProject)

    # Verify the project has the expected properties
    assert project.id == test_project.id
    assert project.name == test_project.name
    assert project.description == test_project.description


def test_create_project(client, test_team_name):
    """Test creating a project."""
    # Create a unique name
    unique_name = f"Test Create Project {str(uuid.uuid4())[:8]}"

    # Create a project
    project = client.projects.create(
        name=unique_name,
        team_name=test_team_name,
        description="This is a test project for testing project creation"
    )

    try:
        # Verify the project was created with the correct properties
        assert project is not None
        assert project.name == unique_name
        assert project.description == "This is a test project for testing project creation"
    finally:
        # Clean up - delete the project
        client.projects.delete(project.id)


def test_update_project(client, test_project):
    """Test updating a project."""
    # Create update data
    new_name = f"Updated Project {str(uuid.uuid4())[:8]}"
    new_description = "This project has been updated"

    # Update the project
    updated_project = client.projects.update(
        test_project.id,
        name=new_name,
        description=new_description
    )

    # Verify the project was updated
    assert updated_project is not None
    assert updated_project.name == new_name
    assert updated_project.description == new_description


def test_delete_project(client, test_team_name):
    """Test deleting a project."""
    # Create a project to delete
    project = client.projects.create(
        name=f"Project to Delete {str(uuid.uuid4())[:8]}",
        team_name=test_team_name,
        description="This project will be deleted"
    )

    # Delete the project
    result = client.projects.delete(project.id)

    # Verify the project was deleted
    assert result is True

    # Verify the project no longer exists
    with pytest.raises(ValueError):
        client.projects.get(project.id)


def test_get_all_projects(client, test_team_name):
    """Test getting all projects."""
    # Create a test project to ensure we have at least one
    project = client.projects.create(
        name=f"Test All Projects {str(uuid.uuid4())[:8]}",
        team_name=test_team_name,
        description="This project is for testing get_all"
    )

    try:
        # Get all projects
        projects = client.projects.get_all()

        # Verify we got at least one project
        assert len(projects) > 0

        # Verify our test project is in the results
        assert project.id in projects

        # Verify the returned project is a LinearProject instance
        assert isinstance(projects[project.id], LinearProject)

    finally:
        # Clean up - delete the project
        client.projects.delete(project.id)


def test_get_projects_by_team(client, test_team_name):
    """Test getting projects filtered by team."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Create a test project for this team
    project = client.projects.create(
        name=f"Test Team Projects {str(uuid.uuid4())[:8]}",
        team_name=test_team_name,
        description="This project is for testing get_all with team filter"
    )

    try:
        # Get projects for this team
        projects = client.projects.get_all(team_id=team_id)

        # Verify we got at least one project
        assert len(projects) > 0

        # Verify our test project is in the results
        assert project.id in projects

    finally:
        # Clean up - delete the project
        client.projects.delete(project.id)


def test_get_id_by_name(client, test_project, test_team_name):
    """Test getting a project ID by its name."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get project ID by name
    project_id = client.projects.get_id_by_name(test_project.name, team_id)

    # Verify we got the correct ID
    assert project_id == test_project.id


def test_create_project_with_invalid_team(client):
    """Test creating a project with an invalid team name."""
    # Try to create a project with a non-existent team
    with pytest.raises(ValueError):
        client.projects.create(
            name="Invalid Team Project",
            team_name="NonExistentTeam"
        )


def test_delete_nonexistent_project(client):
    """Test deleting a non-existent project."""
    # Try to delete a project with a non-existent ID
    with pytest.raises(ValueError):
        client.projects.delete("non-existent-project-id")
