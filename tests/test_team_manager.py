"""
Tests for the TeamManager class.

This module tests the functionality of the TeamManager class.
"""

import pytest

from linear_api import LinearClient, LinearUser
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


def test_state_with_issue_ids(client, test_team_name):
    """Test getting states with issue IDs."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get states without issue IDs first
    states_without_ids = client.teams.get_states(team_id, include_issue_ids=False)

    # Verify states are returned
    assert len(states_without_ids) > 0

    for state in states_without_ids:
        if hasattr(state, 'issue_ids'):
            assert state.issue_ids is None

    # Now get states with issue IDs
    states_with_ids = client.teams.get_states(team_id, include_issue_ids=True)

    # Verify states are returned
    assert len(states_with_ids) > 0

    # Verify issue_ids is a list for states
    for state in states_with_ids:
        assert hasattr(state, 'issue_ids')
        assert isinstance(state.issue_ids, list)

    # Verify the state objects have all new fields
    for state in states_with_ids:
        # Basic fields that should always be present
        assert state.id is not None
        assert state.name is not None
        assert state.color is not None
        assert state.type is not None

        # New fields added
        assert hasattr(state, 'archivedAt')
        assert hasattr(state, 'createdAt')
        assert hasattr(state, 'updatedAt')
        assert hasattr(state, 'description')
        assert hasattr(state, 'position')
        assert hasattr(state, 'inheritedFrom')


def test_get_labels(client, test_team_name):
    """Test getting labels for a team."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get labels
    labels = client.teams.get_labels(team_id)

    # Skip test if no labels are available
    if not labels:
        pytest.skip("No labels available for testing")

    # Verify we got a list of labels
    assert isinstance(labels, list)

    # Verify the returned labels have the expected structure
    for label in labels:
        # Basic fields
        assert hasattr(label, 'id')
        assert hasattr(label, 'name')
        assert hasattr(label, 'color')

        # New fields
        assert hasattr(label, 'archivedAt')
        assert hasattr(label, 'createdAt')
        assert hasattr(label, 'updatedAt')
        assert hasattr(label, 'description')
        assert hasattr(label, 'isGroup')
        assert hasattr(label, 'inheritedFrom')

        if label.creator:
            assert hasattr(label.creator, 'id')
            assert hasattr(label.creator, 'name')


def test_labels_with_issue_ids(client, test_team_name):
    """Test getting labels with issue IDs."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get labels without issue IDs
    labels_without_ids = client.teams.get_labels(team_id)

    # Skip test if no labels are available
    if not labels_without_ids:
        pytest.skip("No labels available for testing")

    # Verify issue_ids is not present
    for label in labels_without_ids:
        assert not hasattr(label, 'issue_ids') or label.issue_ids is None

    # Now get labels with issue IDs
    labels_with_ids = client.teams.get_labels(team_id, include_issue_ids=True)

    # Verify issue_ids is present and is a list
    for label in labels_with_ids:
        assert hasattr(label, 'issue_ids')
        assert isinstance(label.issue_ids, list) or label.issue_ids is None


def test_team_extended_fields(client, test_team_name):
    """Test that the team model includes all the extended fields."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get the team
    team = client.teams.get(team_id)

    # Basic fields
    assert team.id == team_id
    assert team.name == test_team_name
    assert team.key is not None

    # Extended fields
    assert hasattr(team, 'archivedAt')
    assert hasattr(team, 'displayName')
    assert hasattr(team, 'private')
    assert hasattr(team, 'timezone')

    # Configuration parameters
    assert hasattr(team, 'autoArchivePeriod')
    assert hasattr(team, 'autoCloseChildIssues')
    assert hasattr(team, 'autoCloseParentIssues')
    assert hasattr(team, 'autoClosePeriod')
    assert hasattr(team, 'autoCloseStateId')

    # Cycle parameters
    assert hasattr(team, 'cycleDuration')
    assert hasattr(team, 'cycleStartDay')
    assert hasattr(team, 'cyclesEnabled')
    assert hasattr(team, 'cycleCooldownTime')
    assert hasattr(team, 'cycleCalenderUrl')
    assert hasattr(team, 'cycleLockToActive')
    assert hasattr(team, 'cycleIssueAutoAssignCompleted')
    assert hasattr(team, 'cycleIssueAutoAssignStarted')

    # Estimation parameters
    assert hasattr(team, 'defaultIssueEstimate')
    assert hasattr(team, 'issueEstimationType')
    assert hasattr(team, 'issueEstimationAllowZero')
    assert hasattr(team, 'issueEstimationExtended')
    assert hasattr(team, 'inheritIssueEstimation')

    # Other settings
    assert hasattr(team, 'inviteHash')
    assert hasattr(team, 'issueCount')
    assert hasattr(team, 'joinByDefault')
    assert hasattr(team, 'groupIssueHistory')
    assert hasattr(team, 'inheritWorkflowStatuses')
    assert hasattr(team, 'setIssueSortOrderOnStateChange')
    assert hasattr(team, 'requirePriorityToLeaveTriage')
    assert hasattr(team, 'triageEnabled')

    # SCIM Parameters
    assert hasattr(team, 'scimGroupName')
    assert hasattr(team, 'scimManaged')

    # AI parameters
    assert hasattr(team, 'aiThreadSummariesEnabled')


def test_get_members(client, test_team_name):
    """Test getting members of a team."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get members
    members = client.teams.get_members(team_id)

    # Verify we got a list
    assert isinstance(members, list)

    # Skip the rest if no members are available
    if not members:
        pytest.skip("No members available for testing")

    # Verify the members are LinearUser instances
    for member in members:
        assert hasattr(member, 'id')
        assert hasattr(member, 'name')
        assert hasattr(member, 'email')
        assert hasattr(member, 'displayName')


def test_get_active_cycle(client, test_team_name):
    """Test getting the active cycle for a team."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get active cycle
    active_cycle = client.teams.get_active_cycle(team_id)

    # Active cycle might be None if there's no active cycle
    if active_cycle is None:
        # This is a valid state, so we'll just pass the test
        return

    # Verify the active cycle has the expected structure
    assert "id" in active_cycle
    assert "name" in active_cycle
    assert "number" in active_cycle
    assert "startsAt" in active_cycle
    assert "endsAt" in active_cycle


def test_get_cycles(client, test_team_name):
    """Test getting cycles for a team."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get cycles
    cycles = client.teams.get_cycles(team_id)

    # Verify we got a list
    assert isinstance(cycles, list)

    # Skip the rest if no cycles are available
    if not cycles:
        pytest.skip("No cycles available for testing")

    # Verify each cycle has the expected structure
    for cycle in cycles:
        assert "id" in cycle
        assert "name" in cycle
        assert "number" in cycle
        assert "startsAt" in cycle
        assert "endsAt" in cycle


def test_get_templates(client, test_team_name):
    """Test getting templates for a team."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get templates
    templates = client.teams.get_templates(team_id)

    # Verify we got a list
    assert isinstance(templates, list)

    # Skip the rest if no templates are available
    if not templates:
        pytest.skip("No templates available for testing")

    # Verify each template has the expected structure
    for template in templates:
        assert "id" in template
        assert "name" in template
        assert "type" in template  # Template type (issue, project, etc.)


def test_get_label_children(client, test_team_name):
    """Test getting child labels for a team."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get all labels for the team
    labels = client.teams.get_labels(team_id)

    # Skip test if no labels
    if not labels:
        pytest.skip("No labels available for testing")

    # Find a label that might be a parent (has isGroup=True)
    parent_label = next((label for label in labels if getattr(label, 'isGroup', False)), None)

    # If no parent label found, skip test
    if not parent_label:
        pytest.skip("No parent labels available for testing")

    # Get child labels
    children = client.teams.get_label_children(parent_label.id)

    # Verify result structure
    assert isinstance(children, list)

    # Check each child
    for child in children:
        assert hasattr(child, 'id')
        assert hasattr(child, 'name')
        assert hasattr(child, 'color')


def test_get_parent(client):
    """Test getting a parent team."""
    # Get all teams
    teams = client.teams.get_all()

    # Find a team that might have a parent
    child_team = None
    for team_id, team in teams.items():
        if hasattr(team, 'parentId') and team.parentId:
            child_team = team
            break

    # Skip test if no team with parent found
    if not child_team:
        pytest.skip("No team with parent found for testing")

    # Get the parent team
    parent_team = client.teams.get_parent(child_team.id)

    # Verify the result is a team
    assert isinstance(parent_team, LinearTeam)
    assert parent_team.id == child_team.parentId


def test_get_triage_responsibility(client, test_team_name):
    """Test getting triage responsibility data for a team."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get triage responsibility
    triage_data = client.teams.get_triage_responsibility(team_id)

    # Triage may not be set up for all teams, so just verify the structure
    assert isinstance(triage_data, dict)

    # If triage is set up, check expected fields
    if triage_data:
        if 'id' in triage_data:
            assert isinstance(triage_data['id'], str)
        if 'scope' in triage_data:
            assert isinstance(triage_data['scope'], (str, int, float))
        if 'user' in triage_data and triage_data['user']:
            assert isinstance(triage_data['user'], LinearUser)


def test_get_children(client):
    """Test getting child teams for a team."""
    # Get all teams
    teams = client.teams.get_all()

    # Find a parent team (one that other teams refer to as parent)
    parent_team = None
    for team_id, team in teams.items():
        # Check if any team has this team as parent
        for other_id, other_team in teams.items():
            if hasattr(other_team, 'parentId') and other_team.parentId == team_id:
                parent_team = team
                break
        if parent_team:
            break

    # Skip test if no parent team found
    if not parent_team:
        pytest.skip("No parent team found for testing")

    # Get children teams
    children = client.teams.get_children(parent_team.id)

    # Verify the result is a list of teams
    assert isinstance(children, list)
    assert len(children) > 0

    # Check each child
    for child in children:
        assert isinstance(child, LinearTeam)
        assert hasattr(child, 'parentId')
        assert child.parentId == parent_team.id


def test_get_issues(client, test_team_name):
    """Test getting issues for a team using the team manager."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get issues for the team
    issues = client.teams.get_issues(team_id)

    # Verify the result is a list
    assert isinstance(issues, list)

    # Check each issue has expected structure
    for issue in issues:
        assert 'id' in issue
        assert 'title' in issue
        assert 'description' in issue or issue.get('description') is None
        assert 'state' in issue
        assert 'type' in issue['state']


def test_get_webhooks(client, test_team_name):
    """Test getting webhooks for a team."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get webhooks
    webhooks = client.teams.get_webhooks(team_id)

    # Verify the result is a list (might be empty if no webhooks are set up)
    assert isinstance(webhooks, list)

    # If webhooks exist, check their structure
    for webhook in webhooks:
        assert 'id' in webhook
        assert 'label' in webhook
        assert 'url' in webhook
        assert 'enabled' in webhook


def test_team_membership_property(client, test_team_name):
    """Test that the team model's membership property works."""
    # First, get the team ID by name
    team_id = client.teams.get_id_by_name(test_team_name)

    # Then get the team by ID
    team = client.teams.get(team_id)

    try:
        membership = team.membership
        print(f"Got membership: {membership}")
    except Exception as e:
        assert False, f"Failed to access membership property: {e}"


def test_team_properties(client, test_team_name):
    """Test that team properties work correctly with _client reference."""
    # Get the team
    team_id = client.teams.get_id_by_name(test_team_name)
    team = client.teams.get(team_id)

    # Test property access - verify they don't raise exceptions
    # Children property
    children = team.children
    assert isinstance(children, list)

    # Members property
    members = team.members
    assert isinstance(members, list)

    # Active cycle property
    active_cycle = team.activeCycle
    # May be None if no active cycle, but shouldn't raise exception

    # Issues property
    issues = team.issues
    assert isinstance(issues, list)

    # Membership property
    try:
        membership = team.membership
        # Membership may be None, but should not raise exception due to missing _client
    except Exception as e:
        assert False, f"Failed to access membership property: {e}"
