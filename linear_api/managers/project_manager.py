"""
Project manager for Linear API.

This module provides the ProjectManager class for working with Linear projects.
"""

from datetime import datetime
from typing import Dict, Optional, List, Any

from .base_manager import BaseManager
from ..domain import (
    LinearProject, ProjectStatus, FrequencyResolutionType, ProjectStatusType,
    LinearUser, ProjectMilestone, Comment, LinearTeam, ProjectUpdate,
    Document, EntityExternalLink, LinearLabel, CustomerNeed, ProjectRelation, ProjectHistory, LinearIssue
)
from ..utils import process_project_data, enrich_with_client


class ProjectManager(BaseManager[LinearProject]):
    """
    Manager for working with Linear projects.

    This class provides methods for creating, retrieving, updating, and deleting
    projects in Linear, as well as retrieving related information such as members,
    milestones, issues, etc.
    """

    @enrich_with_client
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
                    contentState
                    createdAt
                    updatedAt
                    archivedAt
                    restoredAt
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

    @enrich_with_client
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

    @enrich_with_client
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

    @enrich_with_client
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
            query GetProjectsByTeam($teamId: String!, $cursor: String) {
                team(id: $teamId) {
                    projects(first: 50, after: $cursor) {
                        nodes {
                            id
                            name
                            description
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
            }
            """

            # Get projects using our improved helper method
            response = self._execute_query(query, {"teamId": team_id, "cursor": None})

            if not response or "team" not in response:
                return {}

            project_nodes = self._handle_pagination(
                query,
                {"teamId": team_id},
                ["team", "projects", "nodes"]
            )
        else:
            query = """
            query GetAllProjects($cursor: String) {
                projects(first: 50, after: $cursor) {
                    nodes {
                        id
                        name
                        description
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
            """

            # Get projects using our improved helper method
            project_nodes = self._handle_pagination(
                query,
                {},
                ["projects", "nodes"]
            )

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
            query GetProjectsByTeam($teamId: String!, $cursor: String) {
                team(id: $teamId) {
                    projects(first: 50, after: $cursor) {
                        nodes {
                            id
                            name
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
            }
            """

            # Get the projects using our improved helper method
            response = self._execute_query(query, {"teamId": team_id, "cursor": None})

            if not response or "team" not in response:
                raise ValueError(f"Team with ID {team_id} not found")

            projects = self._handle_pagination(
                query,
                {"teamId": team_id},
                ["team", "projects", "nodes"]
            )
        else:
            query = """
            query GetAllProjects($cursor: String) {
                projects(first: 50, after: $cursor) {
                    nodes {
                        id
                        name
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
            """

            # Get the projects using our improved helper method
            projects = self._handle_pagination(
                query,
                {},
                ["projects", "nodes"]
            )

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

    @enrich_with_client
    def get_members(self, project_id: str) -> List[LinearUser]:
        """
        Get members of a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of LinearUser objects
        """
        # Check cache first
        cached_members = self._cache_get("members_by_project", project_id)
        if cached_members:
            return cached_members

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            members(first: 50, after: $cursor) {
              nodes {
                id
                name
                displayName
                email
                avatarUrl
                createdAt
                updatedAt
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Get the members using our improved helper method with automatic model conversion
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        members = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "members", "nodes"],
            LinearUser  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("members_by_project", project_id, members)

        return members

    def get_milestones(self, project_id: str) -> List[ProjectMilestone]:
        """
        Get milestones for a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of ProjectMilestone objects
        """
        # Check cache first
        cached_milestones = self._cache_get("milestones_by_project", project_id)
        if cached_milestones:
            return cached_milestones

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            projectMilestones(first: 50, after: $cursor) {
              nodes {
                id
                name
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Get the milestones using our improved helper method with automatic model conversion
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        milestones = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "projectMilestones", "nodes"],
            ProjectMilestone  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("milestones_by_project", project_id, milestones)

        return milestones

    def get_comments(self, project_id: str) -> List[Comment]:
        """
        Get comments for a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of Comment objects
        """
        # Check cache first
        cached_comments = self._cache_get("comments_by_project", project_id)
        if cached_comments:
            return cached_comments

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            comments(first: 50, after: $cursor) {
              nodes {
                id
                body
                createdAt
                updatedAt
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Use our extract_and_cache helper for simpler implementation
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        comments = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "comments", "nodes"],
            Comment  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("comments_by_project", project_id, comments)

        return comments

    @enrich_with_client
    def get_issues(self, project_id: str) -> List[LinearIssue]:
        """
        Get issues for a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of issue data dictionaries
        """
        # Check cache first
        cached_issues = self._cache_get("issues_by_project", project_id)
        if cached_issues:
            return cached_issues

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            issues(first: 50, after: $cursor) {
              nodes {
                id
                title
                description
                state {
                  id
                  name
                  type
                }
                priority
                priorityLabel
                createdAt
                updatedAt
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Use our extract_and_cache helper for simpler implementation
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        issues = self._extract_and_cache(
            response,
            ["project", "issues"],
            "issues_by_project",
            project_id
        )

        return issues

    def get_project_updates(self, project_id: str) -> List[ProjectUpdate]:
        """
        Get updates for a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of ProjectUpdate objects
        """
        # Check cache first
        cached_updates = self._cache_get("updates_by_project", project_id)
        if cached_updates:
            return cached_updates

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            projectUpdates(first: 50, after: $cursor) {
              nodes {
                id
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Use our improved helper method with automatic model conversion
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        updates = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "projectUpdates", "nodes"],
            ProjectUpdate  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("updates_by_project", project_id, updates)

        return updates

    def get_relations(self, project_id: str) -> List[ProjectRelation]:
        """
        Get relations for a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of ProjectRelation objects
        """
        # Check cache first
        cached_relations = self._cache_get("relations_by_project", project_id)
        if cached_relations:
            return cached_relations

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            relations(first: 50, after: $cursor) {
              nodes {
                id
                createdAt
                updatedAt
                archivedAt
                type
                anchorType
                relatedAnchorType
                relatedProject {
                  id
                  name
                }
                user {
                  id
                  name
                  displayName
                }
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        relations = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "relations", "nodes"],
            ProjectRelation
        )

        # Cache the result
        self._cache_set("relations_by_project", project_id, relations)

        return relations

    @enrich_with_client
    def get_teams(self, project_id: str) -> List[LinearTeam]:
        """
        Get teams associated with a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of LinearTeam objects
        """
        # Check cache first
        cached_teams = self._cache_get("teams_by_project", project_id)
        if cached_teams:
            return cached_teams

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            teams(first: 50, after: $cursor) {
              nodes {
                id
                name
                key
                description
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Use our improved helper method with automatic model conversion
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        teams = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "teams", "nodes"],
            LinearTeam  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("teams_by_project", project_id, teams)

        return teams

    def get_documents(self, project_id: str) -> List[Document]:
        """
        Get documents associated with a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of Document objects
        """
        # Check cache first
        cached_documents = self._cache_get("documents_by_project", project_id)
        if cached_documents:
            return cached_documents

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            documents(first: 50, after: $cursor) {
              nodes {
                id
                title
                icon
                createdAt
                updatedAt
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Use our improved helper method with automatic model conversion
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        documents = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "documents", "nodes"],
            Document  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("documents_by_project", project_id, documents)

        return documents

    def get_external_links(self, project_id: str) -> List[EntityExternalLink]:
        """
        Get external links associated with a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of EntityExternalLink objects
        """
        # Check cache first
        cached_links = self._cache_get("external_links_by_project", project_id)
        if cached_links:
            return cached_links

        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            externalLinks(first: 50, after: $cursor) {
              nodes {
                id
                url
                label
                createdAt
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Use our improved helper method with automatic model conversion
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        links = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "externalLinks", "nodes"],
            EntityExternalLink  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("external_links_by_project", project_id, links)

        return links

    def get_history(self, project_id: str) -> List[ProjectHistory]:
        """
        Get the history of a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of ProjectHistory objects
        """
        # Check cache first
        cached_history = self._cache_get("history_by_project", project_id)
        if cached_history:
            return cached_history

        query = """
        query($projectId: String!, $cursor: String) {
         project(id: $projectId) {
           history(first: 50, after: $cursor) {
             nodes {
               id
               createdAt
               updatedAt
               archivedAt
               entries
             }
             pageInfo {
               hasNextPage
               endCursor
             }
           }
         }
        }
        """

        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        history = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "history", "nodes"],
            ProjectHistory
        )

        # Cache the result
        self._cache_set("history_by_project", project_id, history)

        return history

    def get_initiatives(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get initiatives associated with a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of initiative data dictionaries
        """
        # Check cache first
        cached_initiatives = self._cache_get("initiatives_by_project", project_id)
        if cached_initiatives:
            return cached_initiatives

        query = """
           query($projectId: String!, $cursor: String) {
             project(id: $projectId) {
               initiatives(first: 50, after: $cursor) {
                 nodes {
                   id
                   name
                   description
                   createdAt
                   updatedAt
                 }
                 pageInfo {
                   hasNextPage
                   endCursor
                 }
               }
             }
           }
           """

        # Use our extract_and_cache helper for simpler implementation
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        initiatives = self._extract_and_cache(
            response,
            ["project", "initiatives"],
            "initiatives_by_project",
            project_id
        )

        return initiatives

    def get_labels(self, project_id: str) -> List[LinearLabel]:
        """
        Get labels associated with a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of LinearLabel objects
        """
        # Check cache first
        cached_labels = self._cache_get("labels_by_project", project_id)
        if cached_labels:
            return cached_labels

        query = """
           query($projectId: String!, $cursor: String) {
             project(id: $projectId) {
               labels(first: 50, after: $cursor) {
                 nodes {
                   id
                   name
                   color
                   description
                   createdAt
                   updatedAt
                 }
                 pageInfo {
                   hasNextPage
                   endCursor
                 }
               }
             }
           }
           """

        # Use our improved helper method with automatic model conversion
        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        labels = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "labels", "nodes"],
            LinearLabel  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("labels_by_project", project_id, labels)

        return labels

    def get_needs(self, project_id: str) -> List[CustomerNeed]:
        """
        Get customer needs associated with a project.

        Args:
            project_id: The ID of the project

        Returns:
            A list of CustomerNeed objects
        """
        # Check cache first
        cached_needs = self._cache_get("needs_by_project", project_id)
        if cached_needs:
            return cached_needs

        query = """
           query($projectId: String!, $cursor: String) {
             project(id: $projectId) {
               needs(first: 50, after: $cursor) {
                 nodes {
                   id
                   createdAt
                   updatedAt
                   archivedAt
                   priority
                   body
                   bodyData
                   url
                   creator {
                     id
                     name
                     displayName
                   }
                 }
                 pageInfo {
                   hasNextPage
                   endCursor
                 }
               }
             }
           }
           """

        response = self._execute_query(query, {"projectId": project_id, "cursor": None})

        if not response or "project" not in response:
            return []

        needs = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "needs", "nodes"],
            CustomerNeed
        )

        # Cache the result
        self._cache_set("needs_by_project", project_id, needs)

        return needs

    def invalidate_cache(self) -> None:
        """
        Invalidate all project-related caches.
        This should be called after any mutating operations.
        """
        self._cache_clear()
