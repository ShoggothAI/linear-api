"""
Issue data processor for Linear API.

This module provides utility functions for processing issue data from the Linear API.
"""

from datetime import datetime
from typing import Dict, Any

from ..domain import (
    LinearIssue,
    LinearUser,
    LinearState,
    LinearLabel,
    LinearProject,
    LinearTeam,
    LinearAttachment,
    ProjectStatus,
    ProjectStatusType,
    FrequencyResolutionType,
)


def process_issue_data(data: Dict[str, Any]) -> LinearIssue:
    """
    Process issue data from the Linear API and convert it to a LinearIssue object.

    Args:
        data: The raw issue data from the API

    Returns:
        A LinearIssue object
    """
    # Process attachments
    attachments = []
    if "attachments" in data and "nodes" in data["attachments"]:
        for attachment in data["attachments"]["nodes"]:
            attachment["issueId"] = data["id"]
            attachments.append(LinearAttachment(**attachment))
    data["attachments"] = attachments

    # Process labels
    labels = []
    if "labels" in data and "nodes" in data["labels"]:
        for label in data["labels"]["nodes"]:
            labels.append(LinearLabel(**label))
    data["labels"] = labels

    # Process nested objects
    if "state" in data and data["state"]:
        data["state"] = LinearState(**data["state"])

    if "team" in data and data["team"]:
        data["team"] = LinearTeam(**data["team"])

    if "assignee" in data and data["assignee"]:
        data["assignee"] = LinearUser(**data["assignee"])

    if "project" in data and data["project"]:
        # The GraphQL query only returns id, name, and description for projects
        # but the LinearProject model requires many more fields
        # Add default values for the required fields that are missing
        project_data = data["project"]
        if project_data:
            # Add required fields with default values if they're missing
            current_time = datetime.now()

            defaults = {
                "createdAt": current_time,
                "updatedAt": current_time,
                "slugId": "default-slug",
                "url": f"https://linear.app/project/{project_data['id']}",
                "color": "#000000",
                "priority": 0,
                "priorityLabel": "None",
                "prioritySortOrder": 0.0,
                "sortOrder": 0.0,
                "progress": 0.0,
                "status": {"type": ProjectStatusType.PLANNED},  # Create a ProjectStatus object with type field
                "scope": 0.0,
                "frequencyResolution": FrequencyResolutionType.WEEKLY
            }

            # Add default values for any missing required fields
            for key, value in defaults.items():
                if key not in project_data:
                    project_data[key] = value

            # Convert status dict to ProjectStatus object
            if "status" in project_data and isinstance(project_data["status"], dict):
                project_data["status"] = ProjectStatus(**project_data["status"])

            data["project"] = LinearProject(**project_data)

    # Handle reactionData - API might return a list instead of a dict
    if "reactionData" in data:
        if isinstance(data["reactionData"], list):
            # Convert to empty dict if it's an empty list
            data["reactionData"] = {}  # TODO ?

    # Process datetime fields
    datetime_fields = [
        "createdAt", "updatedAt", "archivedAt", "startedAt", "completedAt",
        "startedTriageAt", "triagedAt", "canceledAt", "autoClosedAt", "autoArchivedAt",
        "addedToProjectAt", "addedToCycleAt", "addedToTeamAt", "slaStartedAt",
        "slaMediumRiskAt", "slaHighRiskAt", "slaBreachesAt", "snoozedUntilAt",
        "suggestionsGeneratedAt", "dueDate"
    ]

    for field in datetime_fields:
        if field in data and data[field]:
            if isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])

    # Handle parent relationship
    if "parent" in data and data["parent"]:
        data["parentId"] = data["parent"]["id"]
    data.pop("parent", None)  # Remove parent field as we've extracted the ID

    # Create the LinearIssue object
    return LinearIssue(**data)
