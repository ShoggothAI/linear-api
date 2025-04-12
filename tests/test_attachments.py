import pytest
from datetime import datetime
from linear_api.issue_manipulation import create_issue, create_attachment, get_linear_issue
from linear_api.domain import LinearIssueInput, LinearPriority, LinearAttachment, LinearAttachmentInput
from linear_api.get_resources import team_name_to_id


@pytest.fixture
def test_team_name():
    """Fixture to get the name of the test team."""
    return "Test"


@pytest.fixture
def test_issue(test_team_name):
    """Create a test issue to use for attachment tests."""
    # Create a new issue
    issue_input = LinearIssueInput(
        title="Test Issue for Attachments",
        teamName=test_team_name,
        description="This is a test issue for testing attachments",
        priority=LinearPriority.MEDIUM
    )

    response = create_issue(issue_input)
    issue_id = response["issueCreate"]["issue"]["id"]

    # Return the issue ID for use in tests
    return issue_id


def test_create_and_get_attachment(test_issue):
    """Test creating an attachment and then retrieving it."""
    # Create an attachment with metadata
    attachment = LinearAttachmentInput(
        url="https://example.com/test-attachment",
        title="Test Attachment",
        subtitle="This is a test attachment",
        metadata={"miro_id": "abcd"},
        issueId=test_issue
    )

    # Create the attachment in Linear
    response = create_attachment(attachment)

    # Verify the response has the expected structure
    assert "attachmentCreate" in response
    assert "success" in response["attachmentCreate"]
    assert response["attachmentCreate"]["success"] is True
    assert "attachment" in response["attachmentCreate"]
    assert "id" in response["attachmentCreate"]["attachment"]

    # Get the attachment ID from the response
    attachment_id = response["attachmentCreate"]["attachment"]["id"]

    # Now retrieve the issue with its attachments
    issue = get_linear_issue(test_issue)

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


def test_create_multiple_attachments(test_issue):
    """Test creating multiple attachments for a single issue."""
    # Create first attachment
    attachment1 = LinearAttachmentInput(
        url="https://example.com/attachment1",
        title="First Attachment",
        subtitle="This is the first test attachment",
        metadata={"miro_id": "abcd1"},
        issueId=test_issue
    )

    # Create second attachment
    attachment2 = LinearAttachmentInput(
        url="https://example.com/attachment2",
        title="Second Attachment",
        subtitle="This is the second test attachment",
        metadata={"miro_id": "abcd2"},
        issueId=test_issue
    )

    # Create both attachments in Linear
    response1 = create_attachment(attachment1)
    response2 = create_attachment(attachment2)

    # Verify both responses indicate success
    assert response1["attachmentCreate"]["success"] is True
    assert response2["attachmentCreate"]["success"] is True

    # Get the attachment IDs
    attachment1_id = response1["attachmentCreate"]["attachment"]["id"]
    attachment2_id = response2["attachmentCreate"]["attachment"]["id"]

    # Now retrieve the issue with its attachments
    issue = get_linear_issue(test_issue)

    # Verify the issue has both attachments
    assert issue.attachments is not None
    assert len(issue.attachments) >= 2

    # Find our attachments in the list
    attachment_ids = [att.id for att in issue.attachments]
    assert attachment1_id in attachment_ids
    assert attachment2_id in attachment_ids

    # Verify the metadata for both attachments
    for att in issue.attachments:
        if att.id == attachment1_id:
            assert att.metadata is not None
            assert "miro_id" in att.metadata
            assert att.metadata["miro_id"] == "abcd1"
        elif att.id == attachment2_id:
            assert att.metadata is not None
            assert "miro_id" in att.metadata
            assert att.metadata["miro_id"] == "abcd2"


def test_attachment_with_multiple_metadata(test_issue):
    """Test creating an attachment with multiple metadata key-value pairs."""
    # Create an attachment with multiple metadata key-value pairs (flat dictionary)
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
        issueId=test_issue
    )

    # Create the attachment in Linear
    response = create_attachment(attachment)

    # Verify the response indicates success
    assert response["attachmentCreate"]["success"] is True

    # Get the attachment ID
    attachment_id = response["attachmentCreate"]["attachment"]["id"]

    # Now retrieve the issue with its attachments
    issue = get_linear_issue(test_issue)

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
    assert "miro_id" in found_attachment.metadata
    assert found_attachment.metadata["miro_id"] == "abcd"

    # Verify other metadata fields
    assert "board_id" in found_attachment.metadata
    assert found_attachment.metadata["board_id"] == "board123"
    assert "width" in found_attachment.metadata
    assert found_attachment.metadata["width"] == 800
    assert "height" in found_attachment.metadata
    assert found_attachment.metadata["height"] == 600
