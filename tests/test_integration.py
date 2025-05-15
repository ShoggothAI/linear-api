"""
Integration tests for the Linear API client.

This module tests the integration between different components
of the Linear API client.
"""
import time

import pytest
import uuid
from datetime import datetime, timedelta

from linear_api import LinearClient
from linear_api.domain import (
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearPriority,
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


def test_comprehensive_model_updates(client, test_team_name):
    """Test that all model updates work together in a comprehensive workflow."""
    import uuid
    import time
    from linear_api.domain import LinearIssueInput, LinearIssueUpdateInput, LinearPriority

    # Get team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get the team with full details
    team = client.teams.get(team_id)

    # Get all states with issue IDs
    states = client.teams.get_states(team_id, include_issue_ids=True)

    # Get all labels with issue IDs
    labels = client.teams.get_labels(team_id, include_issue_ids=True)

    # Create a test issue to work with
    issue_input = LinearIssueInput(
        title=f"Test Comprehensive Model Updates {uuid.uuid4().hex[:8]}",
        teamName=test_team_name,
        description="This is a test issue for comprehensive model testing",
        priority=LinearPriority.MEDIUM,
    )

    issue = client.issues.create(issue_input)

    try:
        # Verify team has all extended fields
        assert hasattr(team, 'displayName')
        assert hasattr(team, 'cyclesEnabled')
        assert hasattr(team, 'issueEstimationType')

        # Verify states have issue_ids field
        for state in states:
            assert hasattr(state, 'issue_ids')
            assert isinstance(state.issue_ids, list) or state.issue_ids is None

        # Verify labels have issue_ids field
        for label in labels:
            assert hasattr(label, 'issue_ids')
            assert isinstance(label.issue_ids, list) or label.issue_ids is None

        # Debug logging
        print("Available states:")
        for idx, state in enumerate(states):
            print(f"  {idx}: ID={state.id}, Name={state.name}, Type={state.type}")

        # Test linkage between models
        if states:
            target_state = None
            for state in states:
                if state.type.lower() != "canceled":
                    target_state = state
                    break

            if not target_state:
                target_state = states[0]

            print(f"Selected target state: ID={target_state.id}, Name={target_state.name}, Type={target_state.type}")

            # Update issue state to target state
            update_data = LinearIssueUpdateInput(
                stateName=target_state.name
            )

            client.issues._cache_clear()
            client.teams._cache_clear()

            updated_issue = client.issues.update(issue.id, update_data)

            print(f"Updated issue state: ID={updated_issue.state.id}, Name={updated_issue.state.name}")

            client.teams._cache_clear()

            time.sleep(2)

            # Refresh states with issue_ids after update
            refreshed_states = client.teams.get_states(team_id, include_issue_ids=True)

            # Find the state we updated to BY ID (не по индексу)
            state = next((s for s in refreshed_states if s.id == updated_issue.state.id), None)

            print(f"Found refreshed state: ID={state.id if state else 'None'}, Name={state.name if state else 'None'}")

            if state and state.issue_ids:
                print(f"Issue IDs in state: {state.issue_ids}")

                assert issue.id in state.issue_ids, f"Issue ID {issue.id} not found in state's issue_ids: {state.issue_ids}"
            else:
                print(f"State has no issue_ids: {state}")
                assert state is not None, f"Could not find state with ID {updated_issue.state.id}"

    finally:
        # Clean up - delete the test issue
        client.issues.delete(issue.id)


def test_create_issue_with_project_and_labels(client, test_team_name, test_project):
    """Test creating an issue with project and labels."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get labels for the team
    labels = client.teams.get_labels(team_id)

    # Skip test if no labels
    if not labels:
        pytest.skip("No labels available for testing")

    # Take the first label
    first_label = labels[0]

    # Create an issue with project and label
    issue_input = LinearIssueInput(
        title=f"Issue with Project and Label {int(time.time())}",
        teamName=test_team_name,
        description="This is a test issue with project and label",
        priority=LinearPriority.MEDIUM,
        projectName=test_project.name,
        labelIds=[first_label.id]
    )

    issue = client.issues.create(issue_input)

    try:
        # Verify the issue has the project and label
        assert issue.project is not None
        assert issue.project.id == test_project.id
        assert issue.labels is not None
        assert len(issue.labels) > 0
        assert issue.labels[0].id == first_label.id

    finally:
        # Clean up - delete the issue
        client.issues.delete(issue.id)


def test_get_project_issues_via_team(client, test_team_name, test_project):
    """Test getting issues for a specific project via the team manager."""
    # Get the team ID
    team_id = client.teams.get_id_by_name(test_team_name)

    # Get issues for the team
    team_issues = client.teams.get_issues(team_id)

    # Get issues for the project
    project_issues = client.issues.get_by_project(test_project.id)

    # Verify that project issues are a subset of team issues
    project_issue_ids = set(issue.id for issue in project_issues.values())

    # Find team issues that are also in the project
    matching_issues = [issue for issue in team_issues
                       if 'project' in issue
                       and issue['project']
                       and issue['project']['id'] == test_project.id]

    # Verify that we can find project issues within team issues
    # Note: The data structures might be different, so we're just checking IDs
    for issue in matching_issues:
        assert issue['id'] in project_issue_ids


def test_user_organization_relationship(client):
    """Test the relationship between users and their organization."""
    # Get the current user
    me = client.users.get_me()

    # Get organization from user
    org = me.organization

    # The organization might be None depending on API access
    if not org:
        pytest.skip("User has no organization information available")

    # Verify organization structure
    assert hasattr(org, 'id')
    assert hasattr(org, 'name')

    # Get a team to check the relationship
    teams = client.teams.get_all()
    if not teams:
        pytest.skip("No teams available for testing")

    team = next(iter(teams.values()))

    # Check if team has the same organization
    assert hasattr(team, 'organization')
    if team.organization:
        assert team.organization.id == org.id


def test_client_reference_enrich(client, test_team_name, test_project):
    """Test that models are properly enriched with client reference."""
    # Get test objects
    team = client.teams.get(client.teams.get_id_by_name(test_team_name))

    # Check that _client exists and is properly set
    assert hasattr(team, "_client")
    assert team._client is client

    # Test nested objects have client reference too
    if team.defaultIssueState:
        assert hasattr(team.defaultIssueState, "_client")
        assert team.defaultIssueState._client is client

    # Test that project has client reference
    assert hasattr(test_project, "_client")
    assert test_project._client is client

    # Create a test issue
    from linear_api.domain import LinearIssueInput

    issue_input = LinearIssueInput(
        title=f"Test Client Reference {int(time.time())}",
        teamName=test_team_name
    )

    issue = client.issues.create(issue_input)

    try:
        # Check the issue has client reference
        assert hasattr(issue, "_client")
        assert issue._client is client

        # Check the issue's team has client reference
        assert hasattr(issue.team, "_client")
        assert issue.team._client is client

        # Get user and check client reference
        me = client.users.get_me()
        assert hasattr(me, "_client")
        assert me._client is client
    finally:
        # Clean up
        client.issues.delete(issue.id)
