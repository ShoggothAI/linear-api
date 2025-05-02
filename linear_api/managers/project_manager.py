"""
Project manager for Linear API.

This module provides the ProjectManager class for working with Linear projects.
"""

from datetime import datetime
from typing import Dict, Optional

from .base_manager import BaseManager
from ..domain import LinearProject, ProjectStatus


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
        # Используем упрощенный запрос
        query = """
        query GetProject($projectId: String!) {
            project(id: $projectId) {
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
            }
        }
        """

        response = self._execute_query(query, {"projectId": project_id})

        if not response or "project" not in response or response["project"] is None:
            raise ValueError(f"Project with ID {project_id} not found")

        # Convert the response to a LinearProject object
        from ..utils.project_processor import process_project_data
        project = process_project_data(response["project"])

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

        # Update the project
        response = self._execute_query(update_project_mutation, {"id": project_id, "input": kwargs})

        if not response or not response.get("projectUpdate", {}).get("success", False):
            raise ValueError(f"Failed to update project with ID: {project_id}")

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

        return True

    def get_all(self, team_id: Optional[str] = None) -> Dict[str, LinearProject]:
        """
        Get all projects, optionally filtered by team.

        Args:
            team_id: Optional team ID to filter projects by

        Returns:
            A dictionary mapping project IDs to LinearProject objects
        """
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

        # Создаем базовые объекты LinearProject без запроса всех деталей
        projects = {}

        # Текущее время для значений по умолчанию
        current_time = datetime.now()

        # Импортируем необходимые типы
        from ..domain import ProjectStatusType, FrequencyResolutionType

        for project_data in project_nodes:
            try:
                # Добавляем необходимые поля со значениями по умолчанию
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

                # Преобразуем status в объект ProjectStatus
                project_data["status"] = ProjectStatus(**project_data["status"])

                # Создаем объект LinearProject
                project = LinearProject(**project_data)
                projects[project.id] = project
            except Exception as e:
                # Логируем ошибку, но продолжаем с другими проектами
                print(f"Error creating project from data {project_data}: {e}")

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
        # Проверяем, есть ли у нас кэш
        if not hasattr(self, '_project_name_cache'):
            self._project_name_cache = {}

        # Создаем ключ кэша
        cache_key = (project_name, team_id)

        # Проверяем, есть ли проект в кэше
        if cache_key in self._project_name_cache:
            return self._project_name_cache[cache_key]

        # Если нет в кэше, получаем все проекты
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

        # Обновляем кэш
        for project in projects:
            if "name" in project and "id" in project:
                self._project_name_cache[(project["name"], team_id)] = project["id"]

        # Проверяем, есть ли теперь проект в кэше
        if cache_key in self._project_name_cache:
            return self._project_name_cache[cache_key]

        # Если все еще не найден, генерируем ошибку
        team_info = f" in team {team_id}" if team_id else ""
        raise ValueError(f"Project '{project_name}'{team_info} not found")
