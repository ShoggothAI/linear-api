"""
Tests for the UserManager class.

This module tests the functionality of the UserManager class.
"""

import pytest
from datetime import datetime

from linear_api import LinearClient, LinearTeam
from linear_api.domain import LinearUser


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


def test_get_me(client):
    """Test getting the current user."""
    # Get the current user
    me = client.users.get_me()

    # Verify the user is a LinearUser instance
    assert isinstance(me, LinearUser)

    # Verify the user has the expected properties
    assert me.id is not None
    assert me.name is not None
    assert me.email is not None
    assert isinstance(me.createdAt, datetime)
    assert isinstance(me.updatedAt, datetime)


def test_get_user(client):
    """Test getting a user by ID."""
    # First, get the current user to have a valid user ID
    me = client.users.get_me()

    # Then get the user by ID
    user = client.users.get(me.id)

    # Verify the user is a LinearUser instance
    assert isinstance(user, LinearUser)

    # Verify the user has the expected properties
    assert user.id == me.id
    assert user.name == me.name
    assert user.email == me.email
    assert isinstance(user.createdAt, datetime)
    assert isinstance(user.updatedAt, datetime)


def test_get_all_users(client):
    """Test getting all users."""
    # Get all users
    users = client.users.get_all()

    # Verify we got a dictionary
    assert isinstance(users, dict)

    # Verify we got at least one user
    assert len(users) > 0

    # Verify the returned users are LinearUser instances
    for user in users.values():
        assert isinstance(user, LinearUser)
        assert user.id is not None
        assert user.name is not None
        assert user.email is not None


def test_get_email_map(client):
    """Test getting a mapping of user IDs to emails."""
    # Get the email map
    email_map = client.users.get_email_map()

    # Verify we got a dictionary
    assert isinstance(email_map, dict)

    # Verify we got at least one entry
    assert len(email_map) > 0

    # Verify the dictionary has the expected structure
    for user_id, email in email_map.items():
        assert isinstance(user_id, str)
        assert isinstance(email, str)
        assert '@' in email  # Simple email validation


def test_get_id_by_email(client):
    """Test getting a user ID by email."""
    # First, get the current user to have a valid email
    me = client.users.get_me()

    # Then get the user ID by email
    user_id = client.users.get_id_by_email(me.email)

    # Verify we got the correct ID
    assert user_id == me.id


def test_get_id_by_name(client):
    """Test getting a user ID by name."""
    # First, get the current user to have a valid name
    me = client.users.get_me()

    # Then get the user ID by name
    user_id = client.users.get_id_by_name(me.name)

    # Verify we got the correct ID
    assert user_id == me.id


def test_get_nonexistent_user(client):
    """Test getting a non-existent user."""
    # Try to get a user with a non-existent ID
    with pytest.raises(ValueError):
        client.users.get("non-existent-user-id")


def test_get_id_by_nonexistent_email(client):
    """Test getting a user ID by a non-existent email."""
    # Try to get a user ID by a non-existent email
    with pytest.raises(ValueError):
        client.users.get_id_by_email("non-existent-email@example.com")


def test_get_id_by_nonexistent_name(client):
    """Test getting a user ID by a non-existent name."""
    # Try to get a user ID by a non-existent name
    with pytest.raises(ValueError):
        client.users.get_id_by_name("Non Existent User")


def test_fuzzy_name_matching(client):
    """Test that get_id_by_name does fuzzy matching."""
    # First, get the current user to have a valid name
    me = client.users.get_me()

    # Then try to get the user ID with a variant of the name

    # 1. Try lowercase variant
    lower_name = me.name.lower()
    if lower_name != me.name:  # Only test if the name actually changes
        user_id = client.users.get_id_by_name(lower_name)
        assert user_id == me.id

    # 2. Try uppercase variant
    upper_name = me.name.upper()
    if upper_name != me.name:  # Only test if the name actually changes
        user_id = client.users.get_id_by_name(upper_name)
        assert user_id == me.id

    # 3. Try with partial name (just first part if name contains a space)
    if ' ' in me.name:
        first_name = me.name.split(' ')[0]
        user_id = client.users.get_id_by_name(first_name)
        assert user_id == me.id


def test_user_admin_field(client):
    """Test that the user has the admin field."""
    # Get the current user
    me = client.users.get_me()

    # Verify the user has the admin field
    assert hasattr(me, 'admin')
    assert isinstance(me.admin, bool)


def test_user_organization_field(client):
    """Test that the user has the organization field."""
    # Get the current user
    me = client.users.get_me()

    # Verify the user has the organization field
    assert hasattr(me, 'organization')

    # The organization field might be None, but if it's not, it should have the expected structure
    if me.organization:
        assert hasattr(me.organization, 'id')
        assert hasattr(me.organization, 'name')


def test_get_team_memberships(client):
    """Test getting team memberships for a user."""
    # Get the current user
    me = client.users.get_me()

    # Get team memberships
    memberships = client.users.get_team_memberships(me.id)

    # Verify the result is a list
    assert isinstance(memberships, list)

    # Check each membership
    for membership in memberships:
        assert 'id' in membership
        assert 'team' in membership
        assert isinstance(membership['team'], LinearTeam)


def test_get_teams(client):
    """Test getting teams that a user is a member of."""
    # Get the current user
    me = client.users.get_me()

    # Get teams
    teams = client.users.get_teams(me.id)

    # Verify the result is a list
    assert isinstance(teams, list)

    # Check each team
    for team in teams:
        assert isinstance(team, LinearTeam)
        assert hasattr(team, 'id')
        assert hasattr(team, 'name')


def test_get_created_issues(client):
    """Test getting issues created by a user."""
    # Get the current user
    me = client.users.get_me()

    # Get created issues
    issues = client.users.get_created_issues(me.id)

    # Verify the result is a list
    assert isinstance(issues, list)

    # Check each issue
    for issue in issues:
        assert 'id' in issue
        assert 'title' in issue


def test_get_drafts(client):
    """Test getting document drafts created by a user."""
    # Get the current user
    me = client.users.get_me()

    # Get drafts
    drafts = client.users.get_drafts(me.id)

    # Verify the result is a list (might be empty if no drafts)
    assert isinstance(drafts, list)


def test_get_issue_drafts(client):
    """Test getting issue drafts created by a user."""
    # Get the current user
    me = client.users.get_me()

    # Get issue drafts
    drafts = client.users.get_issue_drafts(me.id)

    # Verify the result is a list (might be empty if no drafts)
    assert isinstance(drafts, list)


def test_user_properties(client):
    """Test that user properties work correctly with _client reference."""
    # Get the current user
    me = client.users.get_me()

    # Test property access - verify they don't raise exceptions
    # Assigned issues property
    assigned_issues = me.assignedIssues
    assert isinstance(assigned_issues, dict)

    # Created issues property
    created_issues = me.createdIssues
    assert isinstance(created_issues, list)

    # Teams property
    teams = me.teams
    assert isinstance(teams, list)

    # Team memberships property
    team_memberships = me.teamMemberships
    assert isinstance(team_memberships, list)
