"""
Tests for the IssueManager class.

This module tests the functionality of the IssueManager class.
"""

import pytest
import time
import uuid
from datetime import datetime, timedelta

from linear_api import LinearClient
from linear_api.domain import (
    LinearIssue,
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearPriority,
    LinearState,
    SLADayCountType,
)


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
def test_issue(client, test_team_name):
    """Create a test issue and clean up after the test."""
    # Create a unique issue name using timestamp to avoid conflicts
    issue_name = f"Test Issue {int(time.time())}"

    # Create the issue
    issue_input = LinearIssueInput(
        title=issue_name,
        teamName=test_team_name,
        description="This is a test issue created by automated tests",
        priority=LinearPriority.MEDIUM,
    )

    issue = client.issues.create(issue_input)

    # Return the issue for use in tests
    yield issue

    # Clean up after the test by deleting the issue
    try:
        client.issues.delete(issue.id)
    except ValueError:
        # Issue might have already been deleted in the test
        pass


def test_get_issue(client, test_issue):
    """Test getting an issue by ID."""
    # Get the issue
    issue = client.issues.get(test_issue.id)

    # Verify the issue is a LinearIssue instance
    assert isinstance(issue, LinearIssue)

    # Verify the issue has the expected properties
    assert issue.id == test_issue.id
    assert issue.title == test_issue.title
    assert issue.description == test_issue.description

    # Verify nested objects are properly processed
    assert issue.state is not None
    assert isinstance(issue.state, LinearState)
    assert issue.team is not None


def test_create_issue(client, test_team_name):
    """Test creating an issue."""
    # Create a unique title
    unique_title = f"Test Create Issue {str(uuid.uuid4())[:8]}"

    # Create an issue
    issue_input = LinearIssueInput(
        title=unique_title,
        teamName=test_team_name,
        description="This is a test issue for testing issue creation",
        priority=LinearPriority.HIGH,
    )

    issue = client.issues.create(issue_input)

    try:
        # Verify the issue was created with the correct properties
        assert issue is not None
        assert issue.title == unique_title
        assert issue.description == "This is a test issue for testing issue creation"
        assert issue.priority == LinearPriority.HIGH
    finally:
        # Clean up - delete the issue
        client.issues.delete(issue.id)


def test_update_issue(client, test_issue):
    """Test updating an issue."""
    # Create update data
    new_title = f"Updated Title {str(uuid.uuid4())[:8]}"
    update_data = LinearIssueUpdateInput(
        title=new_title,
        description="This issue has been updated",
        priority=LinearPriority.LOW,
    )

    # Update the issue
    updated_issue = client.issues.update(test_issue.id, update_data)

    # Verify the issue was updated
    assert updated_issue is not None
    assert updated_issue.title == new_title
    assert updated_issue.description == "This issue has been updated"
    assert updated_issue.priority == LinearPriority.LOW


def test_delete_issue(client, test_team_name):
    """Test deleting an issue."""
    # Create an issue to delete
    issue_input = LinearIssueInput(
        title=f"Issue to Delete {str(uuid.uuid4())[:8]}",
        teamName=test_team_name,
        description="This issue will be deleted",
    )

    issue = client.issues.create(issue_input)

    # Delete the issue
    result = client.issues.delete(issue.id)

    # Verify the deletion was successful
    assert result is True

    # Verify the issue is marked as trashed
    deleted_issue = client.issues.get(issue.id)
    assert deleted_issue.trashed is True
    assert deleted_issue.archivedAt is not None


def test_get_by_team(client, test_team_name):
    """Test getting issues by team."""
    # Create some test issues
    test_issue_ids = []

    try:
        # Create 3 test issues with different priorities
        for i, priority in enumerate(
                [LinearPriority.HIGH, LinearPriority.MEDIUM, LinearPriority.LOW]
        ):
            unique_id = str(uuid.uuid4())[:8]
            issue_input = LinearIssueInput(
                title=f"Test Team Issue {i + 1} - {unique_id}",
                description=f"This is a test issue {i + 1} created for testing get_by_team",
                teamName=test_team_name,
                priority=priority,
                metadata={"test_id": unique_id, "test_type": "get_by_team"},
            )

            issue = client.issues.create(issue_input)
            test_issue_ids.append(issue.id)

        # Get issues for the test team
        issues = client.issues.get_by_team(test_team_name)

        # Check that we got at least the issues we created
        assert len(issues) >= len(test_issue_ids)

        # Check that all our test issues are in the results
        for issue_id in test_issue_ids:
            assert issue_id in issues

        # Check the test issues
        for issue_id in test_issue_ids:
            issue = issues[issue_id]
            assert isinstance(issue, LinearIssue)
            assert issue.title.startswith("Test Team Issue")

    finally:
        # Clean up - delete the test issues
        for issue_id in test_issue_ids:
            try:
                client.issues.delete(issue_id)
            except ValueError:
                pass


def test_create_issue_with_parent(client, test_team_name):
    """Test creating an issue with a parent-child relationship."""
    parent_id = None
    child_id = None

    try:
        # Create a parent issue
        parent_input = LinearIssueInput(
            title=f"Parent Issue {str(uuid.uuid4())[:8]}",
            teamName=test_team_name,
            description="This is a parent issue",
        )

        parent = client.issues.create(parent_input)
        parent_id = parent.id

        # Create a child issue
        child_input = LinearIssueInput(
            title=f"Child Issue {str(uuid.uuid4())[:8]}",
            teamName=test_team_name,
            description="This is a child issue",
            parentId=parent_id,
        )

        child = client.issues.create(child_input)
        child_id = child.id

        # Verify the parent-child relationship
        child_issue = client.issues.get(child_id)
        assert child_issue.parentId == parent_id

    finally:
        # Clean up - delete the child issue first, then the parent
        if child_id:
            try:
                client.issues.delete(child_id)
            except ValueError:
                pass

        if parent_id:
            try:
                client.issues.delete(parent_id)
            except ValueError:
                pass


def test_create_issue_with_metadata(client, test_team_name):
    """Test creating an issue with metadata."""
    # Create a test issue with metadata
    metadata = {
        "test_key": "test_value",
        "numeric_value": 42,
        "boolean_value": True,
    }

    issue_input = LinearIssueInput(
        title=f"Issue with Metadata {str(uuid.uuid4())[:8]}",
        teamName=test_team_name,
        description="This issue has metadata attached",
        metadata=metadata,
    )

    issue = client.issues.create(issue_input)

    try:
        # Retrieve the issue to check its metadata
        retrieved_issue = client.issues.get(issue.id)

        # Verify the metadata
        assert "test_key" in retrieved_issue.metadata
        assert retrieved_issue.metadata["test_key"] == "test_value"
        assert "numeric_value" in retrieved_issue.metadata
        assert retrieved_issue.metadata["numeric_value"] == 42

    finally:
        # Clean up - delete the issue
        client.issues.delete(issue.id)


def test_create_issue_with_additional_fields(client, test_team_name):
    """Test creating an issue with additional fields."""
    # Create a unique title
    unique_title = f"Test Additional Fields {str(uuid.uuid4())[:8]}"

    # Create a test issue with additional fields
    issue_input = LinearIssueInput(
        title=unique_title,
        teamName=test_team_name,
        description="This is a test issue with additional fields",
        priority=LinearPriority.HIGH,
        sortOrder=100.0,
        prioritySortOrder=50.0,
        slaType=SLADayCountType.ALL,
        dueDate=datetime.now() + timedelta(days=7),
        metadata={"test_type": "additional_fields", "automated": True}
    )

    issue = client.issues.create(issue_input)

    try:
        # Verify the issue was created with the correct basic properties
        assert issue.title == unique_title
        assert issue.description == "This is a test issue with additional fields"
        assert issue.priority == LinearPriority.HIGH

        # Other fields might not be returned exactly as set due to server-side processing
    finally:
        # Clean up - delete the issue
        client.issues.delete(issue.id)


def test_get_attachments(client, test_issue):
    """Test getting attachments for an issue."""
    # Get attachments for the issue
    attachments = client.issues.get_attachments(test_issue.id)

    # Verify we got a list (might be empty if the issue has no attachments)
    assert isinstance(attachments, list)


def test_get_comments(client, test_issue):
    """Test getting comments for an issue."""
    # Get comments for the issue
    comments = client.issues.get_comments(test_issue.id)

    # Verify we got a list (might be empty if the issue has no comments)
    assert isinstance(comments, list)


def test_get_history(client, test_issue):
    """Test getting history for an issue."""
    # Get history for the issue
    history = client.issues.get_history(test_issue.id)

    # Verify we got a list (might be empty for a new issue)
    assert isinstance(history, list)


def test_get_issue_children(client, test_issue):
    """Test getting child issues for an issue."""
    # Create a child issue for testing
    from linear_api.domain import LinearIssueInput, LinearPriority

    child_input = LinearIssueInput(
        title=f"Child of test_issue {test_issue.id}",
        teamName=test_issue.team.name,
        description="This is a child issue created for testing get_children",
        priority=LinearPriority.MEDIUM,
        parentId=test_issue.id
    )

    child_issue = client.issues.create(child_input)

    try:
        # Get children
        children = client.issues.get_children(test_issue.id)

        # Verify we got a dictionary
        assert isinstance(children, dict)

        # Verify the child issue is in the returned dictionary
        assert child_issue.id in children

        # Verify the child has the correct parent
        assert children[child_issue.id].parentId == test_issue.id

    finally:
        # Clean up - delete the child issue
        client.issues.delete(child_issue.id)


def test_get_issue_subscribers(client, test_issue):
    """Test getting subscribers of an issue."""
    # Get subscribers
    subscribers = client.issues.get_subscribers(test_issue.id)

    # Verify we got a list
    assert isinstance(subscribers, list)

    # Skip the rest if no subscribers (common for test issues)
    if not subscribers:
        return

    # Verify each subscriber is a LinearUser instance
    for subscriber in subscribers:
        assert hasattr(subscriber, 'id')
        assert hasattr(subscriber, 'name')
        assert hasattr(subscriber, 'email')


def test_get_reactions(client, test_issue):
    """Test getting reactions to an issue."""
    # Get reactions
    reactions = client.issues.get_reactions(test_issue.id)

    # Verify the result is a list (might be empty for a new issue)
    assert isinstance(reactions, list)


def test_get_relations(client, test_issue):
    """Test getting relations for an issue."""
    # Get relations
    relations = client.issues.get_relations(test_issue.id)

    # Verify the result is a list (might be empty for a new issue)
    assert isinstance(relations, list)


def test_get_inverse_relations(client, test_issue):
    """Test getting inverse relations for an issue."""
    # Get inverse relations
    relations = client.issues.get_inverse_relations(test_issue.id)

    # Verify the result is a list (might be empty for a new issue)
    assert isinstance(relations, list)


def test_get_needs(client, test_issue):
    """Test getting customer needs associated with an issue."""
    # Get needs
    needs = client.issues.get_needs(test_issue.id)

    # Verify the result is a list (might be empty for a new issue)
    assert isinstance(needs, list)


def test_issue_properties(client, test_issue):
    """Test that issue properties work correctly with _client reference."""
    # Get the issue
    issue = client.issues.get(test_issue.id)

    # Test property access - verify they don't raise exceptions
    # Parent property (might be None but shouldn't raise exception)
    parent = issue.parent

    # Children property
    children = issue.children
    assert isinstance(children, dict)

    # Comments property
    comments = issue.comments
    assert isinstance(comments, list)

    # History property
    history = issue.history
    assert isinstance(history, list)

    # Relations property
    relations = issue.relations
    assert isinstance(relations, list)

    # Subscribers property
    subscribers = issue.subscribers
    assert isinstance(subscribers, list)
