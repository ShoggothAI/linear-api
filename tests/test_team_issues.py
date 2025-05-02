import pytest
import uuid

from linear_api.issue_manipulation import get_team_issues, create_issue, delete_issue
from linear_api.domain import LinearPriority, LinearState, LinearUser, LinearIssueInput


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"  # Using the test team


def test_get_team_issues(test_team_name):
    """Test that get_team_issues returns issues with all the expected fields."""
    # Create some test issues
    test_issue_ids = []
    try:
        # Create 3 test issues with different priorities
        for i, priority in enumerate(
            [LinearPriority.HIGH, LinearPriority.MEDIUM, LinearPriority.LOW]
        ):
            unique_id = str(uuid.uuid4())[:8]
            issue_input = LinearIssueInput(
                title=f"Test Issue {i+1} - {unique_id}",
                description=f"This is a test issue {i+1} created for testing get_team_issues",
                teamName=test_team_name,
                priority=priority,
                metadata={"test_id": unique_id, "test_type": "get_team_issues"},
            )
            response = create_issue(issue_input)
            issue_id = response["issueCreate"]["issue"]["id"]
            test_issue_ids.append(issue_id)
            print(f"Created test issue {i+1} with ID: {issue_id}")

        # Get issues for the test team
        issues = get_team_issues(test_team_name)

        # Check that we got at least the issues we created
        assert len(issues) >= len(test_issue_ids), "Not all created issues were found"

        # Check that all our test issues are in the results
        for issue_id in test_issue_ids:
            assert issue_id in issues, f"Created issue {issue_id} not found in results"

        # Check the first test issue
        test_issue = issues[test_issue_ids[0]]

        # Check that the issue has the expected fields
        assert "id" in test_issue
        assert "title" in test_issue
        assert "identifier" in test_issue
        assert "priority" in test_issue
        assert "state" in test_issue
        assert "number" in test_issue

        # Check that the nested objects are properly processed
        assert isinstance(test_issue["state"], LinearState)

        # Priority should be a LinearPriority enum
        assert isinstance(test_issue["priority"], LinearPriority)
        assert test_issue["priority"] == LinearPriority.HIGH  # First issue was HIGH priority

        # If the issue has an assignee, it should be a LinearUser
        if "assignee" in test_issue and test_issue["assignee"]:
            assert isinstance(test_issue["assignee"], LinearUser)

        # Print some information about the issues
        print(f"Found {len(issues)} issues for team '{test_team_name}'")
        print(f"Test issue: {test_issue['title']} ({test_issue['identifier']})")
        print(f"State: {test_issue['state'].name}")
        print(f"Priority: {test_issue['priority'].name}")

    finally:
        # Clean up - delete the test issues
        for issue_id in test_issue_ids:
            try:
                delete_issue(issue_id)
                print(f"Deleted test issue with ID: {issue_id}")
            except Exception as e:
                print(f"Failed to delete test issue {issue_id}: {e}")


if __name__ == "__main__":
    # This allows running the test directly
    issues = test_get_team_issues("Test")  # Using the test team

    # Print more details about the test issues
    if issues:
        # Get one of our test issues
        test_issue_ids = [id for id in issues.keys() if "Test Issue" in issues[id]["title"]]
        if test_issue_ids:
            test_issue_id = test_issue_ids[0]
            test_issue = issues[test_issue_id]
            print("\nAdditional fields:")
            for field_name in [
                "createdAt",
                "updatedAt",
                "dueDate",
                "startedAt",
                "completedAt",
                "trashed",
                "estimate",
                "priorityLabel",
            ]:
                if field_name in test_issue:
                    value = test_issue[field_name]
                    print(f"{field_name}: {value}")
