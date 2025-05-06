"""
Tests for the TeamManager class.

This module tests the functionality of the TeamManager class.
"""

import pytest

from linear_api import LinearClient
from linear_api.domain import LinearTeam, LinearState


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


def test_get_team(client, test_team_name):
    """Test getting a team by ID."""
    # First, get the team ID by name
    team_id = client.teams.get_id_by_name(test_team_name)

    # Then get the team by ID
    team = client.teams.get(team_id)

    # Verify the team is a LinearTeam instance
    assert isinstance(team, LinearTeam)

    # Verify the team has the expected properties
    assert team.id == team_id
    assert team.name == test_team_name
    assert team.key is not None


def test_get_all_teams(client):
    """Test getting all teams."""
    # Get all teams
    teams = client.teams.get_all()

    # Verify we got a dictionary
    assert isinstance(teams, dict)

    # Verify we got at least one team
    assert len(teams) > 0

    # Verify the returned teams are LinearTeam instances
    for team in teams.values():
        assert isinstance(team, LinearTeam)


def test_get_id_by_name(client, test_team_name):
    """Test getting a team ID by its name."""
    # Get team ID by name
    team_id = client.teams.get_id_by_name(test_team_name)

    # Verify we got a string
    assert isinstance(team_id, str)

    # Verify the ID is not empty
    assert team_id


def test_get_states(client, test_team_name):
    """Test getting workflow states for a team."""
    # First, get the team ID by name
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get states for the team
    states = client.teams.get_states(team_id)

    # Verify we got a list
    assert isinstance(states, list)

    # Verify we got at least one state
    assert len(states) > 0

    # Verify the returned states are LinearState instances
    for state in states:
        assert isinstance(state, LinearState)
        assert state.name is not None
        assert state.color is not None
        assert state.type is not None


def test_get_state_id_by_name(client, test_team_name):
    """Test getting a state ID by its name within a team."""
    # First, get the team ID by name
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get states for the team
    states = client.teams.get_states(team_id)

    # Skip test if no states are available
    if not states:
        pytest.skip("No states available for testing")

    # Get the first state name
    state_name = states[0].name

    # Get state ID by name
    state_id = client.teams.get_state_id_by_name(state_name, team_id)

    # Verify we got a string
    assert isinstance(state_id, str)

    # Verify the ID is not empty
    assert state_id

    # Verify the ID matches the expected state ID
    assert state_id == states[0].id


def test_get_nonexistent_team():
    """Test getting a non-existent team."""
    # Get the API key from environment variable
    import os
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        pytest.skip("LINEAR_API_KEY environment variable not set")

    # Create the client
    client = LinearClient(api_key=api_key)

    # Try to get a team ID by a non-existent name
    with pytest.raises(ValueError):
        client.teams.get_id_by_name("NonExistentTeam")


def test_get_nonexistent_state(client, test_team_name):
    """Test getting a non-existent state."""
    # First, get the team ID by name
    team_id = client.teams.get_id_by_name(test_team_name)

    # Try to get a state ID by a non-existent name
    with pytest.raises(ValueError):
        client.teams.get_state_id_by_name("NonExistentState", team_id)


def test_state_cache(client, test_team_name):
    """Test that states are cached for a team."""
    # First, get the team ID by name
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get states for the team (first call)
    states1 = client.teams.get_states(team_id)

    # Get states for the team again (should use cache)
    states2 = client.teams.get_states(team_id)

    # Verify both calls returned the same states
    assert len(states1) == len(states2)

    # Verify the states have the same IDs
    state_ids1 = [state.id for state in states1]
    state_ids2 = [state.id for state in states2]
    assert set(state_ids1) == set(state_ids2)
