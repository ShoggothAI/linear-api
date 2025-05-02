"""
Tests for attachment functionality.

This module tests the functionality of creating and retrieving attachments.
"""

import pytest
from datetime import datetime

from linear_api import LinearClient
from linear_api.domain import (
    LinearIssueInput,
    LinearPriority,
    LinearAttachment,
    LinearAttachmentInput
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
    """Create a test issue to use for attachment tests."""
    # Create a unique issue title
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    # Create a new issue
    issue_input = LinearIssueInput(
        title=f"Test Issue for Attachments {unique_id}",
        teamName=test_team_name,
        description="This is a test issue for testing attachments",
        priority=LinearPriority.MEDIUM
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


def test_create_and_get_attachment(client, test_issue):
    """Test creating an attachment and then retrieving it."""
    # Create an attachment with metadata
    attachment = LinearAttachmentInput(
        url="https://example.com/test-attachment",
        title="Test Attachment",
        subtitle="This is a test attachment",
        metadata={"miro_id": "abcd"},
        issueId=test_issue.id
    )

    # Create the attachment
    response = client.issues.create_attachment(attachment)

    # Verify the response has the expected structure
    assert response is not None
    assert "attachmentCreate" in response
    assert "success" in response["attachmentCreate"]
    assert response["attachmentCreate"]["success"] is True
    assert "attachment" in response["attachmentCreate"]
    assert "id" in response["attachmentCreate"]["attachment"]

    # Get the attachment ID from the response
    attachment_id = response["attachmentCreate"]["attachment"]["id"]

    # Now retrieve the issue with its attachments
    issue = client.issues.get(test_issue.id)

    # Verify the issue has the attachment
    assert issue.attachments is not None
    assert len(issue.attachments) > 0

    # Find our attachment in the list
    found_attachment = None
    for att in issue.attachments:
        if att.id == attachment_id:
            found_attachment = att
            break

    # Verify we found the attachment
    assert found_attachment is not None
    assert found_attachment.url == "https://example.com/test-attachment"
    assert found_attachment.title == "Test Attachment"
    assert found_attachment.subtitle == "This is a test attachment"
    assert found_attachment.metadata is not None
    assert "miro_id" in found_attachment.metadata
    assert found_attachment.metadata["miro_id"] == "abcd"


def test_create_multiple_attachments(client, test_issue):
    """Test creating multiple attachments for a single issue."""
    # Create first attachment
    attachment1 = LinearAttachmentInput(
        url="https://example.com/attachment1",
        title="First Attachment",
        subtitle="This is the first test attachment",
        metadata={"miro_id": "abcd1"},
        issueId=test_issue.id
    )

    # Create second attachment
    attachment2 = LinearAttachmentInput(
        url="https://example.com/attachment2",
        title="Second Attachment",
        subtitle="This is the second test attachment",
        metadata={"miro_id": "abcd2"},
        issueId=test_issue.id
    )

    # Create both attachments
    response1 = client.issues.create_attachment(attachment1)
    response2 = client.issues.create_attachment(attachment2)

    # Verify both responses indicate success
    assert response1["attachmentCreate"]["success"] is True
    assert response2["attachmentCreate"]["success"] is True

    # Get the attachment IDs
    attachment1_id = response1["attachmentCreate"]["attachment"]["id"]
    attachment2_id = response2["attachmentCreate"]["attachment"]["id"]

    # Get all attachments for the issue
    attachments = client.issues.get_attachments(test_issue.id)

    # Verify there are at least two attachments
    assert len(attachments) >= 2

    # Also get the issue to verify its attachments property
    issue = client.issues.get(test_issue.id)
    assert len(issue.attachments) >= 2

    # Find our attachments in the issue attachments
    attachment_ids = [att.id for att in issue.attachments]
    assert attachment1_id in attachment_ids
    assert attachment2_id in attachment_ids


def test_attachment_with_multiple_metadata(client, test_issue):
    """Test creating an attachment with multiple metadata key-value pairs."""
    # Create an attachment with multiple metadata key-value pairs
    metadata = {
        "miro_id": "abcd",
        "board_id": "board123",
        "item_type": "image",
        "created_by": "user456",
        "width": 800,
        "height": 600
    }

    attachment = LinearAttachmentInput(
        url="https://example.com/multiple-metadata-attachment",
        title="Multiple Metadata Attachment",
        subtitle="This attachment has multiple metadata key-value pairs",
        metadata=metadata,
        issueId=test_issue.id
    )

    # Create the attachment
    response = client.issues.create_attachment(attachment)

    # Verify the response indicates success
    assert response["attachmentCreate"]["success"] is True

    # Get the attachment ID
    attachment_id = response["attachmentCreate"]["attachment"]["id"]

    # Now retrieve the issue with its attachments
    issue = client.issues.get(test_issue.id)

    # Find our attachment in the list
    found_attachment = None
    for att in issue.attachments:
        if att.id == attachment_id:
            found_attachment = att
            break

    # Verify we found the attachment
    assert found_attachment is not None

    # Verify the metadata was stored correctly
    assert found_attachment.metadata is not None

    # Check a few of the metadata fields
    assert "miro_id" in found_attachment.metadata
    assert found_attachment.metadata["miro_id"] == "abcd"
    assert "board_id" in found_attachment.metadata
    assert found_attachment.metadata["board_id"] == "board123"

    # Check numeric fields
    assert "width" in found_attachment.metadata
    assert found_attachment.metadata["width"] == 800
    assert "height" in found_attachment.metadata
    assert found_attachment.metadata["height"] == 600
