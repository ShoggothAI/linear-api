from typing import Optional, Dict, Any

from linear_api.call_linear_api import call_linear_api
from linear_api.domain import LinearProject
from linear_api.get_resources import (
    team_name_to_id,
    LinearResourceType,
    get_resources,
    resource_name_to_id,
)


def create_project(name: str, team_name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new project in Linear.

    Args:
        name: The name of the project
        team_name: The name of the team to create the project in
        description: Optional description for the project

    Returns:
        The response from the Linear API containing the created project information

    Raises:
        ValueError: If the team doesn't exist or the project creation fails
    """
    # Convert team_name to team_id
    team_id = team_name_to_id(team_name)

    # GraphQL mutation to create a project
    create_project_mutation = """
    mutation CreateProject($input: ProjectCreateInput!) {
      projectCreate(input: $input) {
        success
        project {
          id
          name
          description
          createdAt
          updatedAt
          slugId
          url
          color
          priority
          priorityLabel
          prioritySortOrder
          sortOrder
          progress
          status {
            type
          }
          scope
        }
      }
    }
    """

    # Build the input variables
    input_vars = {"name": name, "teamIds": [team_id]}

    # Add optional description if provided
    if description is not None:
        input_vars["description"] = description

    # Prepare the GraphQL request
    project_data = {"query": create_project_mutation, "variables": {"input": input_vars}}

    # Create the project
    response = call_linear_api(project_data)

    # Check if the creation was successful
    if response is None or not response.get("projectCreate", {}).get("success", False):
        raise ValueError(f"Failed to create project '{name}' in team '{team_name}'")

    return response


def delete_project(project_id: str) -> Dict[str, Any]:
    """
    Delete a project by its ID.

    Args:
        project_id: The ID of the project to delete

    Returns:
        The response from the Linear API

    Raises:
        ValueError: If the project doesn't exist or can't be deleted
    """
    # GraphQL mutation to delete a project
    delete_project_mutation = """
    mutation DeleteProject($id: String!) {
        projectDelete(id: $id) {
            success
        }
    }
    """

    # Prepare the GraphQL request
    variables = {"id": project_id}

    # Call the Linear API
    response = call_linear_api({"query": delete_project_mutation, "variables": variables})

    # Check if the deletion was successful
    if response is None or not response.get("projectDelete", {}).get("success", False):
        raise ValueError(f"Failed to delete project with ID: {project_id}")

    return response


def get_project(project_id: str) -> LinearProject:
    """
    Fetch a project by ID using GraphQL API.

    Args:
        project_id: The ID of the project to fetch

    Returns:
        A LinearProject object with the project details

    Raises:
        ValueError: If the project doesn't exist
    """
    query = """
    query GetProject($projectId: String!) {
        project(id: $projectId) {
            # Basic fields
            id
            name
            description
            createdAt
            updatedAt
            slugId
            url
            color
            priority
            priorityLabel
            prioritySortOrder
            sortOrder
            progress
            status {
                type
            }
            scope
            frequencyResolution

            # Optional date fields
            archivedAt
            autoArchivedAt
            canceledAt
            completedAt
            healthUpdatedAt
            startedAt
            projectUpdateRemindersPausedUntilAt

            # Optional content fields
            content
            contentState
            health
            icon
            trashed

            # Optional numeric fields
            updateReminderFrequency
            updateReminderFrequencyInWeeks
            updateRemindersHour

            # Optional complex fields
            startDate
            startDateResolution
            targetDate
            targetDateResolution
            updateRemindersDay

            # Relationships
            creator {
                id
                name
                displayName
                email
            }
            lead {
                id
                name
                displayName
                email
            }
            favorite {
                id
                createdAt
                updatedAt
            }
            lastAppliedTemplate {
                id
                name
            }
            documentContent {
                id
                content
            }

            # We're not fetching complex connection fields to keep the query size manageable
            # These would be populated if needed for specific use cases
        }
    }
    """

    # Call the Linear API
    response = call_linear_api({"query": query, "variables": {"projectId": project_id}})

    # Check if the project was found
    if response is None or "project" not in response or response["project"] is None:
        raise ValueError(f"Project with ID {project_id} not found")

    # Convert the response to a LinearProject object
    project_data = response["project"]
    return LinearProject(**project_data)


def get_projects(team_id: Optional[str] = None) -> Dict[str, str]:
    """Get projects from Linear API."""
    return get_resources(LinearResourceType.PROJECT, team_id)


def project_name_to_id(project_name: str, team_id: Optional[str] = None) -> str:
    """Convert a project name to its ID."""
    return resource_name_to_id(LinearResourceType.PROJECT, project_name, team_id)
