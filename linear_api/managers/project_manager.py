"""
Project manager for Linear API.

This module provides the ProjectManager class for working with Linear projects.
"""

from datetime import datetime
from typing import Dict, Optional

from .base_manager import BaseManager
from ..domain import LinearProject, ProjectStatus, FrequencyResolutionType, ProjectStatusType
from ..utils import process_project_data


class ProjectManager(BaseManager[LinearProject]):
    """
    Manager for working with Linear projects.

    This class provides methods for creating, retrieving, updating, and deleting
    projects in Linear.
    """

    def get(self, project_id: str) -> LinearProject:
        """
        Fetch a project by ID.

        Args:
            project_id: The ID of the project to fetch

        Returns:
            A LinearProject object with the project details

        Raises:
            ValueError: If the project doesn't exist
        """
        # Check cache first
        cached_project = self._cache_get("projects_by_id", project_id)
        if cached_project:
            return cached_project

        # Use a simplified query
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

        response = self._execute_query(query, {"projectId": project_id})

        if not response or "project" not in response or response["project"] is None:
            raise ValueError(f"Project with ID {project_id} not found")

        # Convert the response to a LinearProject object
        project = process_project_data(response["project"])

        # Cache the project
        self._cache_set("projects_by_id", project_id, project)

        return project

    def create(self, name: str, team_name: str, description: Optional[str] = None) -> LinearProject:
        """
        Create a new project in Linear.

        Args:
            name: The name of the project
            team_name: The name of the team to create the project in
            description: Optional description for the project

        Returns:
            The created LinearProject

        Raises:
            ValueError: If the team doesn't exist or the project creation fails
        """
        # Convert team_name to team_id
        team_id = self.client.teams.get_id_by_name(team_name)

        # GraphQL mutation to create a project
        create_project_mutation = """
        mutation CreateProject($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            success
            project {
              id
            }
          }
        }
        """

        # Build the input variables
        input_vars = {"name": name, "teamIds": [team_id]}

        # Add optional description if provided
        if description is not None:
            input_vars["description"] = description

        # Create the project
        response = self._execute_query(create_project_mutation, {"input": input_vars})

        if not response or not response.get("projectCreate", {}).get("success", False):
            raise ValueError(f"Failed to create project '{name}' in team '{team_name}'")

        # Invalidate caches after creation
        self._cache_clear()
        self.client.teams._cache_invalidate("all_teams", "all")  # Also invalidate team cache

        # Return the full project object
        project_id = response["projectCreate"]["project"]["id"]
        return self.get(project_id)

    def update(self, project_id: str, **kwargs) -> LinearProject:
        """
        Update an existing project in Linear.

        Args:
            project_id: The ID of the project to update
            **kwargs: The fields to update (e.g., name, description)

        Returns:
            The updated LinearProject

        Raises:
            ValueError: If the project doesn't exist or can't be updated
        """
        if not kwargs:
            raise ValueError("No update fields provided")

        # GraphQL mutation to update a project
        update_project_mutation = """
        mutation UpdateProject($id: String!, $input: ProjectUpdateInput!) {
          projectUpdate(id: $id, input: $input) {
            success
            project {
              id
            }
          }
        }
        """

        response = self._execute_query(update_project_mutation, {"id": project_id, "input": kwargs})

        if not response or not response.get("projectUpdate", {}).get("success", False):
            raise ValueError(f"Failed to update project with ID: {project_id}")

        # Invalidate caches after update
        self._cache_invalidate("projects_by_id", project_id)
        self._cache_clear("all_projects")

        # Return the updated project
        return self.get(project_id)

    def delete(self, project_id: str) -> bool:
        """
        Delete a project by its ID.

        Args:
            project_id: The ID of the project to delete

        Returns:
            True if the deletion was successful

        Raises:
            ValueError: If the project doesn't exist or can't be deleted
        """
        mutation = """
        mutation DeleteProject($id: String!) {
            projectDelete(id: $id) {
                success
            }
        }
        """

        response = self._execute_query(mutation, {"id": project_id})

        if not response or not response.get("projectDelete", {}).get("success", False):
            raise ValueError(f"Failed to delete project with ID: {project_id}")

        # Invalidate caches after deletion
        self._cache_invalidate("projects_by_id", project_id)
        self._cache_clear("all_projects")
        self._cache_clear("project_ids_by_name")

        return True

    def get_all(self, team_id: Optional[str] = None) -> Dict[str, LinearProject]:
        """
        Get all projects, optionally filtered by team.

        Args:
            team_id: Optional team ID to filter projects by

        Returns:
            A dictionary mapping project IDs to LinearProject objects
        """
        # Check cache first
        cache_key = f"team_{team_id}" if team_id else "all"
        cached_projects = self._cache_get("all_projects", cache_key)
        if cached_projects:
            return cached_projects

        if team_id:
            query = """
            query GetProjectsByTeam($teamId: String!) {
                team(id: $teamId) {
                    projects {
                        nodes {
                            id
                            name
                            description
                        }
                    }
                }
            }
            """

            response = self._execute_query(query, {"teamId": team_id})

            if not response or "team" not in response or not response["team"] or "projects" not in response["team"]:
                return {}

            project_nodes = response["team"]["projects"]["nodes"]
        else:
            query = """
            query GetAllProjects {
                projects {
                    nodes {
                        id
                        name
                        description
                    }
                }
            }
            """

            response = self._execute_query(query)

            if not response or "projects" not in response or "nodes" not in response["projects"]:
                return {}

            project_nodes = response["projects"]["nodes"]

        # Create basic LinearProject objects without requesting all details
        projects = {}

        # Current time for default values
        current_time = datetime.now()

        for project_data in project_nodes:
            try:
                # Add required fields with default values
                project_data.update({
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
                    "status": {"type": ProjectStatusType.PLANNED},
                    "scope": 0.0,
                    "frequencyResolution": FrequencyResolutionType.WEEKLY
                })

                project_data["status"] = ProjectStatus(**project_data["status"])

                project = LinearProject(**project_data)
                projects[project.id] = project

                # Cache individual project
                self._cache_set("projects_by_id", project.id, project)

                # Cache project ID by name
                self._cache_set("project_ids_by_name", (project.name, team_id), project.id)

            except Exception as e:
                print(f"Error creating project from data {project_data}: {e}")

        # Cache all projects
        self._cache_set("all_projects", cache_key, projects)

        return projects

    def get_id_by_name(self, project_name: str, team_id: Optional[str] = None) -> str:
        """
        Get a project ID by its name, optionally within a specific team.

        Args:
            project_name: The name of the project
            team_id: Optional team ID to filter by

        Returns:
            The project ID

        Raises:
            ValueError: If the project is not found
        """
        # Check cache first
        cache_key = (project_name, team_id)
        cached_id = self._cache_get("project_ids_by_name", cache_key)
        if cached_id:
            return cached_id

        if team_id:
            query = """
            query GetProjectsByTeam($teamId: String!) {
                team(id: $teamId) {
                    projects {
                        nodes {
                            id
                            name
                        }
                    }
                }
            }
            """

            response = self._execute_query(query, {"teamId": team_id})

            if not response or "team" not in response or not response["team"] or "projects" not in response["team"]:
                raise ValueError(f"No projects found for team {team_id}")

            projects = response["team"]["projects"]["nodes"]
        else:
            query = """
            query {
                projects {
                    nodes {
                        id
                        name
                    }
                }
            }
            """

            response = self._execute_query(query)

            if not response or "projects" not in response or "nodes" not in response["projects"]:
                raise ValueError("No projects found")

            projects = response["projects"]["nodes"]

        # Cache all project IDs by name
        for project in projects:
            if "name" in project and "id" in project:
                self._cache_set("project_ids_by_name", (project["name"], team_id), project["id"])

        # Check cache again after populating it
        cached_id = self._cache_get("project_ids_by_name", cache_key)
        if cached_id:
            return cached_id

        team_info = f" in team {team_id}" if team_id else ""
        raise ValueError(f"Project '{project_name}'{team_info} not found")

    def invalidate_cache(self) -> None:
        """
        Invalidate all project-related caches.
        This should be called after any mutating operations.
        """
        self._cache_clear()
