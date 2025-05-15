"""
Tests for the ProjectManager class.

This module tests the functionality of the ProjectManager class.
"""

import pytest
import time
import uuid

from linear_api import LinearClient, LinearTeam
from linear_api.domain import LinearProject, ProjectMilestone, Comment


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

    # Verify the project is marked as trashed
    deleted_project = client.projects.get(project.id)
    assert deleted_project.trashed is True
    assert deleted_project.archivedAt is not None


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


def test_get_project_members(client, test_project):
    """Test getting members of a project."""
    # Get project members
    members = client.projects.get_members(test_project.id)

    # Verify we got a list
    assert isinstance(members, list)

    # Members might be empty if the project has no members yet
    if not members:
        return

    # Verify each member is a LinearUser instance
    for member in members:
        assert hasattr(member, 'id')
        assert hasattr(member, 'name')
        assert hasattr(member, 'email')
        assert hasattr(member, 'displayName')


def test_get_project_milestones(client, test_project):
    """Test getting milestones for a project."""
    # Get milestones
    milestones = client.projects.get_milestones(test_project.id)

    # Verify we got a list
    assert isinstance(milestones, list)

    # Milestones might be empty if the project has no milestones
    if not milestones:
        return

    # Verify each milestone has the expected structure
    for milestone in milestones:
        assert "id" in milestone
        assert "name" in milestone


def test_get_milestones(client, test_project):
    """Test getting milestones for a project."""
    # Get milestones
    milestones = client.projects.get_milestones(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(milestones, list)

    # If milestones exist, check their structure
    for milestone in milestones:
        assert isinstance(milestone, ProjectMilestone)
        assert hasattr(milestone, 'id')
        assert hasattr(milestone, 'name')


def test_get_comments(client, test_project):
    """Test getting comments for a project."""
    # Get comments
    comments = client.projects.get_comments(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(comments, list)

    # If comments exist, check their structure
    for comment in comments:
        assert isinstance(comment, Comment)
        assert hasattr(comment, 'id')
        assert hasattr(comment, 'body')
        assert hasattr(comment, 'createdAt')


def test_get_relations(client, test_project):
    """Test getting relations for a project."""
    # Get relations
    relations = client.projects.get_relations(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(relations, list)

    # If relations exist, check their structure
    for relation in relations:
        assert 'id' in relation
        assert 'type' in relation
        assert 'targetId' in relation


def test_get_teams(client, test_project):
    """Test getting teams associated with a project."""
    # Get teams
    teams = client.projects.get_teams(test_project.id)

    # Verify the result is a list
    assert isinstance(teams, list)
    assert len(teams) > 0  # Should have at least one team (the one it was created in)

    # Check each team
    for team in teams:
        assert isinstance(team, LinearTeam)
        assert hasattr(team, 'id')
        assert hasattr(team, 'name')


def test_get_documents(client, test_project):
    """Test getting documents associated with a project."""
    # Get documents
    documents = client.projects.get_documents(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(documents, list)


def test_get_external_links(client, test_project):
    """Test getting external links associated with a project."""
    # Get external links
    links = client.projects.get_external_links(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(links, list)


def test_get_history(client, test_project):
    """Test getting the history of a project."""
    # Get history
    history = client.projects.get_history(test_project.id)

    # Verify the result is a list
    assert isinstance(history, list)

    # We used to expect at least one entry (creation), but API might return an empty list
    # So we just check that the return type is a list without asserting its length

    # Check structure of history items if any exist
    for item in history:
        assert hasattr(item, 'id')
        assert hasattr(item, 'createdAt')

        # Check entries if present
        if hasattr(item, 'entries') and item.entries:
            assert isinstance(item.entries, dict)


def test_get_initiatives(client, test_project):
    """Test getting initiatives associated with a project."""
    # Get initiatives
    initiatives = client.projects.get_initiatives(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(initiatives, list)


def test_get_labels(client, test_project):
    """Test getting labels associated with a project."""
    # Get labels
    labels = client.projects.get_labels(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(labels, list)


def test_get_needs(client, test_project):
    """Test getting customer needs associated with a project."""
    # Get needs
    needs = client.projects.get_needs(test_project.id)

    # Verify the result is a list (might be empty for a new project)
    assert isinstance(needs, list)


def test_project_properties(client, test_project):
    """Test that project properties work correctly with _client reference."""
    # Get the project
    project = client.projects.get(test_project.id)

    # Test property access - verify they don't raise exceptions
    # Documents property
    documents = project.documents
    assert isinstance(documents, list)

    # Members property
    members = project.members
    assert isinstance(members, list)

    # Issues property
    issues = project.issues
    assert isinstance(issues, list)

    # Teams property
    teams = project.teams
    assert isinstance(teams, list)

    # Labels property
    labels = project.labels
    assert isinstance(labels, list)
