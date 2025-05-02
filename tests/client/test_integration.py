"""
Integration tests for the Linear API client.

This module tests the integration between different components
of the Linear API client.
"""

import pytest
import uuid
from datetime import datetime, timedelta

from linear_api import LinearClient
from linear_api.domain import (
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearPriority,
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


def test_create_project_with_issues(client, test_team_name):
    """Test creating a project and adding issues to it."""
    # Create a unique project name
    project_name = f"Test Project {uuid.uuid4().hex[:8]}"

    # Create a project
    project = client.projects.create(
        name=project_name,
        team_name=test_team_name,
        description="This is a test project for integration testing"
    )

    # Create issues in the project
    issue_ids = []
    try:
        # Create 3 issues with different priorities
        for i, priority in enumerate([
            LinearPriority.HIGH,
            LinearPriority.MEDIUM,
            LinearPriority.LOW
        ]):
            issue_input = LinearIssueInput(
                title=f"Test Issue {i + 1} for {project_name}",
                teamName=test_team_name,
                description=f"This is test issue {i + 1} for integration testing",
                priority=priority,
                projectName=project_name
            )

            issue = client.issues.create(issue_input)
            issue_ids.append(issue.id)

        # Get issues for the project
        project_issues = client.issues.get_by_project(project.id)

        # Verify we got at least the issues we created
        assert len(project_issues) >= len(issue_ids)

        # Verify all our issues are in the project issues
        for issue_id in issue_ids:
            assert issue_id in project_issues

    finally:
        # Clean up - delete the issues and project
        for issue_id in issue_ids:
            try:
                client.issues.delete(issue_id)
            except ValueError:
                pass

        try:
            client.projects.delete(project.id)
        except ValueError:
            pass


def test_issue_with_state_workflow(client, test_team_name):
    """Test creating an issue and moving it through workflow states."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get workflow states for the team
    states = client.teams.get_states(team_id)

    # Skip test if not enough states
    if len(states) < 2:
        pytest.skip("Need at least two states for this test")

    # Get "todo" and "done" states (or similar)
    todo_state = next((s for s in states if s.type.lower() == "unstarted"), states[0])
    done_state = next((s for s in states if s.type.lower() == "completed"), states[-1])

    # If we couldn't find clear todo/done states, just use the first and last
    if todo_state == done_state:
        todo_state = states[0]
        done_state = states[-1]

    # Create a unique issue
    issue_name = f"Workflow Test Issue {uuid.uuid4().hex[:8]}"

    # Create the issue in the "todo" state
    issue_input = LinearIssueInput(
        title=issue_name,
        teamName=test_team_name,
        description="This is a test issue for workflow testing",
        stateName=todo_state.name
    )

    issue = client.issues.create(issue_input)

    try:
        # Verify the issue was created in the todo state
        assert issue.state.id == todo_state.id

        # Update the issue to the done state
        update_data = LinearIssueUpdateInput(
            stateName=done_state.name
        )

        updated_issue = client.issues.update(issue.id, update_data)

        # Verify the issue was updated to the done state
        assert updated_issue.state.id == done_state.id

    finally:
        # Clean up - delete the issue
        try:
            client.issues.delete(issue.id)
        except ValueError:
            pass


def test_parent_child_issues(client, test_team_name):
    """Test creating parent and child issues."""
    # Create a parent issue
    parent_name = f"Parent Issue {uuid.uuid4().hex[:8]}"
    parent_input = LinearIssueInput(
        title=parent_name,
        teamName=test_team_name,
        description="This is a parent issue for hierarchy testing"
    )

    parent = client.issues.create(parent_input)

    # Create child issues
    child_ids = []

    try:
        # Create 3 child issues
        for i in range(3):
            child_input = LinearIssueInput(
                title=f"Child Issue {i + 1} of {parent_name}",
                teamName=test_team_name,
                description=f"This is child issue {i + 1} for hierarchy testing",
                parentId=parent.id
            )

            child = client.issues.create(child_input)
            child_ids.append(child.id)

        # Verify each child has the parent ID set
        for child_id in child_ids:
            child = client.issues.get(child_id)
            assert child.parentId == parent.id

    finally:
        # Clean up - delete the child issues first, then the parent
        for child_id in child_ids:
            try:
                client.issues.delete(child_id)
            except ValueError:
                pass

        try:
            client.issues.delete(parent.id)
        except ValueError:
            pass


def test_comprehensive_issue_workflow(client, test_team_name):
    """Test a comprehensive issue workflow with multiple operations."""
    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Create a unique project
    project_name = f"Comprehensive Test Project {uuid.uuid4().hex[:8]}"
    project = client.projects.create(
        name=project_name,
        team_name=test_team_name,
        description="This is a comprehensive test project"
    )

    # Get a workflow state
    states = client.teams.get_states(team_id)
    if not states:
        pytest.skip("No states available for testing")

    initial_state = states[0]

    # Create a comprehensive issue
    issue_input = LinearIssueInput(
        title=f"Comprehensive Test Issue {uuid.uuid4().hex[:8]}",
        teamName=test_team_name,
        description="This is a comprehensive test issue",
        priority=LinearPriority.HIGH,
        projectName=project_name,
        stateName=initial_state.name,
        sortOrder=100.0,
        dueDate=datetime.now() + timedelta(days=7),
        metadata={
            "test_type": "comprehensive",
            "created_by": "test_integration.py",
            "tags": ["test", "integration", "workflow"]
        }
    )

    issue = None

    try:
        # Create the issue
        issue = client.issues.create(issue_input)

        # Verify initial properties
        assert issue.title == issue_input.title
        assert issue.description == issue_input.description
        assert issue.priority == LinearPriority.HIGH
        assert issue.project.name == project_name
        assert issue.state.id == initial_state.id

        # Update the issue
        if len(states) > 1:
            next_state = states[1]
            update_data = LinearIssueUpdateInput(
                stateName=next_state.name,
                priority=LinearPriority.MEDIUM,
                description="This issue has been updated"
            )

            updated_issue = client.issues.update(issue.id, update_data)

            # Verify the updates
            assert updated_issue.state.id == next_state.id
            assert updated_issue.priority == LinearPriority.MEDIUM
            assert updated_issue.description == "This issue has been updated"

        # Create an attachment for the issue
        from linear_api.domain import LinearAttachmentInput

        attachment = LinearAttachmentInput(
            url="https://example.com/comprehensive-test",
            title="Comprehensive Test Attachment",
            subtitle="This is a test attachment for the comprehensive test",
            metadata={"test_id": uuid.uuid4().hex},
            issueId=issue.id
        )

        attachment_response = client.issues.create_attachment(attachment)
        assert attachment_response["attachmentCreate"]["success"] is True

        # Get the issue again to verify it has the attachment
        refreshed_issue = client.issues.get(issue.id)
        assert len(refreshed_issue.attachments) > 0

    finally:
        # Clean up - delete the issue and project
        if issue:
            try:
                client.issues.delete(issue.id)
            except ValueError:
                pass

        try:
            client.projects.delete(project.id)
        except ValueError:
            pass
