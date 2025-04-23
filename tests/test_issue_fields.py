import pytest
from datetime import datetime

from linear_api.issue_manipulation import get_linear_issue
from linear_api.domain import LinearIssue, LinearPriority


def test_get_linear_issue_with_all_fields():
    """Test that get_linear_issue returns a LinearIssue with all available fields."""
    # Use a known issue ID from your Linear account
    # This is just a placeholder - replace with a real issue ID
    issue_id = "4739f616-353c-4782-9e44-935e7b10d0bc"  # Replace with a real issue ID

    # Get the issue
    issue = get_linear_issue(issue_id)

    # Verify that the issue is a LinearIssue
    assert isinstance(issue, LinearIssue)

    # Verify required fields
    assert issue.id is not None
    assert issue.title is not None
    assert issue.url is not None
    assert issue.state is not None
    assert isinstance(issue.priority, LinearPriority)
    assert issue.team is not None
    assert isinstance(issue.createdAt, datetime)
    assert isinstance(issue.updatedAt, datetime)
    assert isinstance(issue.number, int)
    assert isinstance(issue.customerTicketCount, int)

    # Print some of the new fields to verify they're being populated
    print(f"Issue ID: {issue.id}")
    print(f"Title: {issue.title}")
    print(f"Priority: {issue.priority}")
    print(f"Priority Label: {issue.priorityLabel}")
    print(f"Identifier: {issue.identifier}")


if __name__ == "__main__":
    # This allows running the test directly
    issue = test_get_linear_issue_with_all_fields()

    # Print more details about the issue
    print("\nAdditional fields:")
    for field_name in [
        "sortOrder",
        "prioritySortOrder",
        "startedAt",
        "completedAt",
        "trashed",
        "identifier",
        "branchName",
        "descriptionState",
    ]:
        value = getattr(issue, field_name, None)
        print(f"{field_name}: {value}")
