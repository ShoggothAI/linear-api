"""
Project data processor for Linear API.

This module provides utility functions for processing project data from the Linear API.
"""

from datetime import datetime
from typing import Dict, Any

from ..domain import (
    LinearProject,
    LinearUser,
    ProjectStatus,
    Favorite,
    Template,
    DocumentContent,
    TimelessDate,
)


def process_project_data(data: Dict[str, Any]) -> LinearProject:
    """
    Process project data from the Linear API and convert it to a LinearProject object.

    Args:
        data: The raw project data from the API

    Returns:
        A LinearProject object
    """
    # Process nested objects
    if "creator" in data and data["creator"]:
        data["creator"] = LinearUser(**data["creator"])

    if "lead" in data and data["lead"]:
        data["lead"] = LinearUser(**data["lead"])

    if "favorite" in data and data["favorite"]:
        data["favorite"] = Favorite(**data["favorite"])

    if "lastAppliedTemplate" in data and data["lastAppliedTemplate"]:
        data["lastAppliedTemplate"] = Template(**data["lastAppliedTemplate"])

    if "documentContent" in data and data["documentContent"]:
        data["documentContent"] = DocumentContent(**data["documentContent"])

    if "status" in data and data["status"]:
        data["status"] = ProjectStatus(**data["status"])

    # Process datetime fields
    datetime_fields = [
        "createdAt", "updatedAt", "archivedAt", "autoArchivedAt",
        "canceledAt", "completedAt", "healthUpdatedAt", "startedAt",
        "projectUpdateRemindersPausedUntilAt"
    ]

    for field in datetime_fields:
        if field in data and data[field] and isinstance(data[field], str):
            data[field] = datetime.fromisoformat(data[field])

    # Process special date fields
    date_fields = ["startDate", "targetDate"]
    for field in date_fields:
        if field in data and data[field] and isinstance(data[field], dict):
            if all(key in data[field] for key in ["year", "month", "day"]):
                data[field] = TimelessDate(**data[field])

    # Create the LinearProject object
    return LinearProject(**data)
