"""
Team manager for Linear API.

This module provides the TeamManager class for working with Linear teams and team-related resources.
"""

from typing import Dict, List, Any, Optional

from .base_manager import BaseManager
from ..domain import (
    LinearTeam, LinearState, LinearLabel, LinearUser, LinearUserReference, TriageResponsibility, TeamMembership
)
from ..utils import enrich_with_client


class TeamManager(BaseManager[LinearTeam]):
    """
    Manager for working with Linear teams.

    This class provides methods for retrieving teams and team-related resources
    like workflow states.
    """

    @enrich_with_client
    def get(self, team_id: str) -> LinearTeam:
        """
        Fetch a team by ID.

        Args:
            team_id: The ID of the team to fetch

        Returns:
            A LinearTeam object with the team details

        Raises:
            ValueError: If the team doesn't exist
        """
        # Check cache first
        cached_team = self._cache_get("teams_by_id", team_id)
        if cached_team:
            return cached_team

        query = """
        query GetTeam($teamId: String!) {
           team(id: $teamId) {
               id
               name
               key
               description
               color
               icon
               createdAt
               updatedAt
               archivedAt
               displayName
               private
               timezone
        
               parent {
                   id
                   name
                   key
                   description
                   color
                   icon
               }
               posts {
                   id
                   title
                   createdAt
                   updatedAt
               }
               progressHistory
               upcomingCycleCount
        
               # Configuration parameters
               autoArchivePeriod
               autoCloseChildIssues
               autoCloseParentIssues
               autoClosePeriod
               autoCloseStateId
        
               # Cycle parameters
               cycleDuration
               cycleStartDay
               cyclesEnabled
               cycleCooldownTime
               cycleCalenderUrl
               cycleLockToActive
               cycleIssueAutoAssignCompleted
               cycleIssueAutoAssignStarted
        
               # Estimation parameters
               defaultIssueEstimate
               issueEstimationType
               issueEstimationAllowZero
               issueEstimationExtended
               inheritIssueEstimation
        
               # Other settings
               inviteHash
               issueCount
               joinByDefault
               groupIssueHistory
               inheritWorkflowStatuses
               setIssueSortOrderOnStateChange
               requirePriorityToLeaveTriage
               triageEnabled
        
               # SCIM Parameters
               scimGroupName
               scimManaged
        
               # AI parameters
               aiThreadSummariesEnabled
        
               # Default templates и states с типизированными полями
               defaultIssueState {
                   id
                   name
                   type
                   color
               }
               defaultProjectTemplate {
                   id
                   name
               }
               defaultTemplateForMembers {
                   id
                   name
               }
               defaultTemplateForNonMembers {
                   id
                   name
               }
               markedAsDuplicateWorkflowState {
                   id
                   name
                   type
                   color
               }
               triageIssueState {
                   id
                   name
                   type
                   color
               }
        
               organization {
                   id
                   name
               }
               integrationsSettings {
                   id
               }
               currentProgress
               states {
                   nodes {
                       id
                       name
                       color
                       type
                       description
                       position
                   }
                   pageInfo {
                       hasNextPage
                       endCursor
                   }
               }
        
               # Memberships connection
               memberships {
                   nodes {
                       id
                       createdAt
                       updatedAt
                       archivedAt
                       owner
                       sortOrder
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
        
               # Facets - просто запрашиваем id
               facets {
                   id
               }
        
               # GitAutomationStates - с правильными полями
               gitAutomationStates {
                   nodes {
                       id
                       branchPattern
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

        response = self._execute_query(query, {"teamId": team_id})

        if not response or "team" not in response or not response["team"]:
            raise ValueError(f"Team with ID {team_id} not found")

        # Process the team data
        team_data = response["team"]

        if "parent" in team_data and team_data["parent"]:
            team_data["parentId"] = team_data["parent"]["id"]

        if "parent" in team_data:
            team_data.pop("parent")

        # Create the team object
        team = LinearTeam(**team_data)

        # Cache the team
        self._cache_set("teams_by_id", team_id, team)

        return team

    @enrich_with_client
    def get_all(self) -> Dict[str, LinearTeam]:
        """
        Get all teams in the organization.

        Returns:
            A dictionary mapping team IDs to LinearTeam objects
        """
        # Check cache first
        cached_teams = self._cache_get("all_teams", "all")
        if cached_teams:
            return cached_teams

        # Use a simple query only for obtaining IDs and names
        query = """
       query {
           teams {
               nodes {
                   id
                   name
                   key
                   description
               }
           }
       }
       """

        response = self._execute_query(query)

        if not response or "teams" not in response or "nodes" not in response["teams"]:
            return {}

        # Extract team nodes using our helper method
        team_nodes = self._extract_nodes(response, ["teams", "nodes"])

        teams = {}
        for team_data in team_nodes:
            try:
                team = LinearTeam(
                    id=team_data["id"],
                    name=team_data["name"],
                    key=team_data.get("key", ""),
                    description=team_data.get("description", "")
                )
                teams[team.id] = team

                # Cache individual team
                self._cache_set("teams_by_id", team.id, team)

                # Cache team ID by name
                self._cache_set("team_ids_by_name", team.name, team.id)

            except Exception as e:
                print(f"Error creating team from data {team_data}: {e}")

        # Cache all teams
        self._cache_set("all_teams", "all", teams)

        return teams

    def get_id_by_name(self, team_name: str) -> str:
        """
        Get a team ID by its name.

        Args:
            team_name: The name of the team

        Returns:
            The team ID

        Raises:
            ValueError: If the team is not found
        """
        # Check cache first
        cached_id = self._cache_get("team_ids_by_name", team_name)
        if cached_id:
            return cached_id

        query = """
       query {
           teams {
               nodes {
                   id
                   name
               }
           }
       }
       """

        response = self._execute_query(query)

        if not response or "teams" not in response or "nodes" not in response["teams"]:
            raise ValueError("No teams found")

        # Extract team data using our helper
        teams = self._extract_nodes(response, ["teams", "nodes"])

        for team in teams:
            if "name" in team and "id" in team:
                # Cache all mappings for future use
                self._cache_set("team_ids_by_name", team["name"], team["id"])

        # Check cache again after populating it
        cached_id = self._cache_get("team_ids_by_name", team_name)
        if cached_id:
            return cached_id

        raise ValueError(f"Team '{team_name}' not found")

    def get_states(self, team_id: str, include_issue_ids: bool = False, force_refresh: bool = False) -> List[
        LinearState]:
        """
        Get all workflow states for a team.

        Args:
            team_id: The ID of the team
            include_issue_ids: Whether to include issue IDs in the result
            force_refresh: Force refreshing the cache

        Returns:
            A list of LinearState objects
        """
        # Check cache first if not forcing refresh
        cache_key = f"states_by_team_id_{include_issue_ids}"
        if not force_refresh:
            cached_states = self._cache_get(cache_key, team_id)
            if cached_states:
                return cached_states

        # Base query without issues
        base_query = """
       query GetStates($teamId: ID!, $cursor: String) {
           workflowStates(filter: { team: { id: { eq: $teamId } } }, first: 50, after: $cursor) {
               nodes {
                   id
                   name
                   color
                   type
                   archivedAt
                   createdAt
                   updatedAt
                   description
                   position
                   inheritedFrom {
                       id
                       name
                   }
               }
               pageInfo {
                   hasNextPage
                   endCursor
               }
           }
       }
       """

        # Query with issues included
        query_with_issues = """
       query GetStates($teamId: ID!, $cursor: String) {
           workflowStates(filter: { team: { id: { eq: $teamId } } }, first: 50, after: $cursor) {
               nodes {
                   id
                   name
                   color
                   type
                   archivedAt
                   createdAt
                   updatedAt
                   description
                   position
                   inheritedFrom {
                       id
                       name
                   }
                   issues {
                       nodes {
                           id
                       }
                       pageInfo {
                           hasNextPage
                           endCursor
                       }
                   }
               }
               pageInfo {
                   hasNextPage
                   endCursor
               }
           }
       }
       """

        # Use the appropriate query based on include_issue_ids
        query = query_with_issues if include_issue_ids else base_query

        # Get states using our pagination helper
        state_nodes = self._handle_pagination(
            query,
            {"teamId": team_id},
            ["workflowStates", "nodes"]
        )

        states = []
        for state_data in state_nodes:
            if include_issue_ids and "issues" in state_data and "nodes" in state_data["issues"]:
                issue_ids = [issue["id"] for issue in state_data["issues"]["nodes"]]

                # If the issues have more pages, retrieve all pages
                issues_page_info = state_data["issues"]["pageInfo"]
                if issues_page_info.get("hasNextPage", False):
                    # This requires a separate query to get all issue IDs for this state
                    more_issue_ids = self._get_all_issue_ids_for_state(state_data["id"], issues_page_info["endCursor"])
                    issue_ids.extend(more_issue_ids)

                del state_data["issues"]
                state_data["issue_ids"] = issue_ids
            elif "issues" in state_data:
                del state_data["issues"]

            states.append(LinearState(**state_data))

        # Cache the states
        self._cache_set(cache_key, team_id, states)

        # Also cache individual state IDs
        for state in states:
            cache_key_name = f"{team_id}:{state.name}"
            self._cache_set("state_ids_by_name", cache_key_name, state.id)

        return states

    def _get_all_issue_ids_for_state(self, state_id: str, cursor: str) -> List[str]:
        """
        Get all issue IDs for a specific workflow state, handling pagination.

        Args:
            state_id: The ID of the workflow state
            cursor: The pagination cursor to start from

        Returns:
            A list of issue IDs
        """
        query = """
       query($stateId: ID!, $cursor: String) {
         workflowState(id: $stateId) {
           issues(first: 100, after: $cursor) {
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

        # Use our enhanced pagination handler to get all issue nodes
        issue_nodes = self._handle_pagination(
            query,
            {"stateId": state_id},
            ["workflowState", "issues", "nodes"],
            initial_cursor=cursor
        )

        # Extract just the IDs
        return [issue["id"] for issue in issue_nodes]

    def get_state_id_by_name(self, state_name: str, team_id: str) -> str:
        """
        Get a state ID by its name within a team.

        Args:
            state_name: The name of the state
            team_id: The ID of the team the state belongs to

        Returns:
            The state ID

        Raises:
            ValueError: If the state is not found
        """
        # Check cache first
        cache_key = f"{team_id}:{state_name}"
        cached_id = self._cache_get("state_ids_by_name", cache_key)
        if cached_id:
            return cached_id

        # Get all states for this team
        states = self.get_states(team_id)

        # Find the state with the matching name
        for state in states:
            if state.name == state_name:
                # Cache the state ID
                self._cache_set("state_ids_by_name", cache_key, state.id)
                return state.id

        raise ValueError(f"State '{state_name}' not found in team {team_id}")

    @enrich_with_client
    def get_members(self, team_id: str) -> List[LinearUser]:
        """
        Get members of a team.

        Args:
            team_id: The ID of the team

        Returns:
            A list of LinearUser objects
        """
        # Check cache first
        cached_members = self._cache_get("members_by_team", team_id)
        if cached_members:
            return cached_members

        query = """
       query($teamId: String!, $cursor: String) {
         team(id: $teamId) {
           members(first: 50, after: $cursor) {
             nodes {
               id
               name
               displayName
               email
               avatarUrl
               active
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

        # Get the initial response
        response = self._execute_query(query, {"teamId": team_id, "cursor": None})

        if not response or "team" not in response or not response["team"]:
            return []

        # Use our improved method to handle pagination and convert to LinearUser objects
        members = self._handle_pagination(
            query,
            {"teamId": team_id},
            ["team", "members", "nodes"],
            LinearUser  # Specify the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("members_by_team", team_id, members)

        return members

    def get_membership(self, team_id: str, user_id: Optional[str] = None) -> Optional[TeamMembership]:
        """
        Get the membership of a user in a team.

        Args:
            team_id: The ID of the team
            user_id: The ID of the user. If None, current user is used.

        Returns:
            TeamMembership object or None if not found
        """
        # Check cache first
        cache_key = f"{team_id}:{user_id if user_id else 'current'}"
        cached_membership = self._cache_get("membership_by_team_user", cache_key)
        if cached_membership:
            return cached_membership

        try:
            # If user_id not provided, get current user
            if user_id is None:
                try:
                    current_user = self.client.users.get_me()
                    user_id = current_user.id
                except Exception as e:
                    print(f"Failed to get current user: {e}")
                    return None

            query = """
            query GetTeamMembership($teamId: String!, $userId: String!) {
              team(id: $teamId) {
                membership(userId: $userId) {
                  id
                  createdAt
                  updatedAt
                  archivedAt
                  owner
                  sortOrder
                  user {
                    id
                    name
                    displayName
                    email
                  }
                }
              }
            }
            """

            response = self._execute_query(query, {"teamId": team_id, "userId": user_id})

            if (not response or "team" not in response or not response["team"] or
                    "membership" not in response["team"] or not response["team"]["membership"]):
                return None

            membership_data = response["team"]["membership"]

            # Конвертируем user в LinearUser если он есть
            if "user" in membership_data and membership_data["user"]:
                from ..domain import LinearUser
                membership_data["user"] = LinearUser(**membership_data["user"])

            membership = TeamMembership(**membership_data)

            # Cache the result
            self._cache_set("membership_by_team_user", cache_key, membership)

            return membership
        except Exception as e:
            print(f"Failed to get membership for team {team_id} and user {user_id}: {e}")
            return None

    def get_labels(self, team_id: str, include_issue_ids: bool = False) -> List[LinearLabel]:
        """
        Get labels for a team.

        Args:
            team_id: The ID of the team
            include_issue_ids: Whether to include issue IDs in the result

        Returns:
            A list of LinearLabel objects
        """
        # Check cache first
        cache_key = f"labels_by_team_{include_issue_ids}"
        cached_labels = self._cache_get(cache_key, team_id)
        if cached_labels:
            return cached_labels

        base_query = """
        query($teamId: ID!) {
          issueLabels(filter: { team: { id: { eq: $teamId } } }) {
            nodes {
              id
              name
              color
              archivedAt
              createdAt
              updatedAt
              description
              isGroup
              inheritedFrom {
                  id
                  name
              }
              parent {
                  id
                  name
                  color
              }
              creator {
                  id
                  name
                  displayName
                  email
              }
            }
          }
        }
        """

        query_with_issues = """
        query($teamId: ID!, $cursor: String) {
         issueLabels(filter: { team: { id: { eq: $teamId } } }, first: 50, after: $cursor) {
           nodes {
             id
             name
             color
             archivedAt
             createdAt
             updatedAt
             description
             isGroup
             inheritedFrom {
                 id
                 name
             }
             parent {
                 id
                 name
                 color
             }
             creator {
                 id
                 name
                 displayName
             }
             team {
                 id
                 name
                 key
             }
             issues {
               nodes {
                 id
               }
               pageInfo {
                 hasNextPage
                 endCursor
               }
             }
           }
           pageInfo {
             hasNextPage
             endCursor
           }
         }
        }
        """

        query = query_with_issues if include_issue_ids else base_query

        # Use our enhanced pagination method to get all label nodes
        label_nodes = self._handle_pagination(
            query,
            {"teamId": team_id},
            ["issueLabels", "nodes"]
        )

        labels = []
        for label_data in label_nodes:
            if include_issue_ids and "issues" in label_data and "nodes" in label_data["issues"]:
                issue_ids = [issue["id"] for issue in label_data["issues"]["nodes"]]

                # If the issues have more pages, retrieve all pages
                issues_page_info = label_data["issues"]["pageInfo"]
                if issues_page_info.get("hasNextPage", False):
                    # This requires a separate query to get all issue IDs for this label
                    more_issue_ids = self._get_all_issue_ids_for_label(label_data["id"], issues_page_info["endCursor"])
                    issue_ids.extend(more_issue_ids)

                del label_data["issues"]
                label_data["issue_ids"] = issue_ids
            elif "issues" in label_data:
                del label_data["issues"]

            if "team" in label_data and label_data["team"]:
                label_data["team"] = LinearTeam(**label_data["team"])

            if "creator" in label_data and label_data["creator"]:
                label_data["creator"] = LinearUserReference(**label_data["creator"])

            if "parent" in label_data and label_data["parent"]:
                label_data["parent"] = LinearLabel(**label_data["parent"])

            labels.append(LinearLabel(**label_data))

        # Cache the result
        self._cache_set(cache_key, team_id, labels)

        return labels

    def _get_all_issue_ids_for_label(self, label_id: str, cursor: str) -> List[str]:
        """
        Get all issue IDs for a specific label, handling pagination.

        Args:
            label_id: The ID of the label
            cursor: The pagination cursor to start from

        Returns:
            A list of issue IDs
        """
        query = """
       query($labelId: ID!, $cursor: String) {
         issueLabel(id: $labelId) {
           issues(first: 100, after: $cursor) {
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

        # Use our improved pagination handler
        issue_nodes = self._handle_pagination(
            query,
            {"labelId": label_id},
            ["issueLabel", "issues", "nodes"],
            initial_cursor=cursor
        )

        # Extract just the IDs
        return [issue["id"] for issue in issue_nodes]

    def get_label_children(self, label_id: str) -> List[LinearLabel]:
        """
        Get child labels for a label.

        Args:
            label_id: The ID of the parent label

        Returns:
            A list of LinearLabel objects that are children of the given label
        """
        # Check cache first
        cached_children = self._cache_get("label_children", label_id)
        if cached_children:
            return cached_children

        query = """
       query($labelId: String!, $cursor: String) {
         issueLabels(filter: { parent: { id: { eq: $labelId } } }, first: 50, after: $cursor) {
           nodes {
             id
             name
             color
             archivedAt
             createdAt
             updatedAt
             description
             isGroup

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
       """

        # Use our improved method to get all labels and convert them
        children = self._handle_pagination(
            query,
            {"labelId": label_id},
            ["issueLabels", "nodes"],
            LinearLabel  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("label_children", label_id, children)

        return children

    def get_active_cycle(self, team_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the active cycle for a team.

        Args:
            team_id: The ID of the team

        Returns:
            The active cycle data or None if no active cycle
        """
        # Check cache first
        cached_cycle = self._cache_get("active_cycle_by_team", team_id)
        if cached_cycle:
            return cached_cycle

        query = """
       query($teamId: ID!) {
         cycles(filter: { team: { id: { eq: $teamId } }, isActive: { eq: true } }) {
           nodes {
             id
             name
             number
             startsAt
             endsAt
           }
         }
       }
       """

        response = self._execute_query(query, {"teamId": team_id})

        # Use our helper to extract cycle nodes
        cycles = self._extract_nodes(response, ["cycles", "nodes"])

        if not cycles:
            return None

        # Return the first active cycle
        active_cycle = cycles[0]

        # Cache the result
        self._cache_set("active_cycle_by_team", team_id, active_cycle)

        return active_cycle

    def get_cycles(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get cycles for a team.

        Args:
            team_id: The ID of the team

        Returns:
            A list of cycle data
        """
        # Check cache first
        cached_cycles = self._cache_get("cycles_by_team", team_id)
        if cached_cycles:
            return cached_cycles

        query = """
       query($teamId: ID!, $cursor: String) {
         cycles(filter: { team: { id: { eq: $teamId } } }, first: 50, after: $cursor) {
           nodes {
             id
             name
             number
             startsAt
             endsAt
             completedAt
           }
           pageInfo {
             hasNextPage
             endCursor
           }
         }
       }
       """

        # Use our improved pagination handler to get all cycles
        cycles = self._handle_pagination(
            query,
            {"teamId": team_id},
            ["cycles", "nodes"]
        )

        # Cache the result
        self._cache_set("cycles_by_team", team_id, cycles)

        return cycles

    def get_templates(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get templates for a team.

        Args:
            team_id: The ID of the team

        Returns:
            A list of template data
        """
        try:
            # Check cache first
            cached_templates = self._cache_get("templates_by_team", team_id)
            if cached_templates:
                return cached_templates

            team_query = """
           query($teamId: String!, $cursor: String) {
               team(id: $teamId) {
                   id
                   templates(first: 50, after: $cursor) {
                       nodes {
                           id
                           name
                           description
                           type
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

            # Use our extract_and_cache helper to simplify this method
            response = self._execute_query(team_query, {"teamId": team_id, "cursor": None})

            if not response or "team" not in response or not response["team"]:
                return []

            # Use our improved pagination method
            templates = self._handle_pagination(
                team_query,
                {"teamId": team_id},
                ["team", "templates", "nodes"]
            )

            # Cache the result
            self._cache_set("templates_by_team", team_id, templates)

            return templates

        except ValueError as e:
            print(f"Warning: Failed to get templates: {str(e)}")
            return []

    @enrich_with_client
    def get_children(self, team_id: str) -> List[LinearTeam]:
        """
        Get child teams for a team.

        Args:
            team_id: The ID of the parent team

        Returns:
            A list of LinearTeam objects that are children of the given team
        """
        # Check cache first
        cached_children = self._cache_get("children_by_team", team_id)
        if cached_children:
            return cached_children

        query = """
       query($teamId: String!, $cursor: String) {
         teams(filter: { parent: { id: { eq: $teamId } } }, first: 50, after: $cursor) {
           nodes {
             id
             name
             key
             description
             color
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
       """

        # Use our improved pagination method with automatic model conversion
        children = self._handle_pagination(
            query,
            {"teamId": team_id},
            ["teams", "nodes"],
            LinearTeam  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("children_by_team", team_id, children)

        return children

    @enrich_with_client
    def get_issues(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get issues for a team.

        Args:
            team_id: The ID of the team

        Returns:
            A list of issue data dictionaries
        """
        # Check cache first
        cached_issues = self._cache_get("issues_by_team", team_id)
        if cached_issues:
            return cached_issues

        query = """
        query($teamId: String!, $cursor: String) {
          team(id: $teamId) {
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

        # Use our extract_and_cache helper to simplify implementation
        response = self._execute_query(query, {"teamId": team_id, "cursor": None})

        if not response or "team" not in response or not response["team"]:
            return []

        # Get issues using our pagination helper
        issues = self._extract_and_cache(
            response,
            ["team", "issues"],
            "issues_by_team",
            team_id
        )

        return issues

    @enrich_with_client
    def get_projects(self, team_id: str) -> Dict[str, Any]:
        """
        Get projects for a team.

        Args:
            team_id: The ID of the team

        Returns:
            A dictionary containing the team's projects
        """
        # This is essentially a wrapper around the ProjectManager's get_all method
        # with team_id filtering, but we'll implement it here for completeness
        return self.client.projects.get_all(team_id)

    def get_webhooks(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get webhooks for a team.

        Args:
            team_id: The ID of the team

        Returns:
            A list of webhook data
        """
        # Check cache first
        cached_webhooks = self._cache_get("webhooks_by_team", team_id)
        if cached_webhooks:
            return cached_webhooks

        query = """
        query($teamId: String!, $cursor: String) {
          team(id: $teamId) {
            webhooks(first: 50, after: $cursor) {
              nodes {
                id
                label
                url
                enabled
                secret
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

        # Use our improved helper method to handle pagination and extraction
        response = self._execute_query(query, {"teamId": team_id, "cursor": None})

        if not response or "team" not in response or not response["team"]:
            return []

        webhooks = self._extract_and_cache(
            response,
            ["team", "webhooks"],
            "webhooks_by_team",
            team_id
        )

        return webhooks

    @enrich_with_client
    def get_parent(self, team_id: str) -> Optional[LinearTeam]:
        """
        Get the parent team of a team.

        Args:
            team_id: The ID of the team

        Returns:
            The parent LinearTeam object or None if the team has no parent
        """
        # Check cache first
        cached_parent = self._cache_get("parent_by_team", team_id)
        if cached_parent is not None:  # Can be None if team has no parent
            return cached_parent

        query = """
        query($teamId: String!) {
          team(id: $teamId) {
            parent {
              id
              name
              key
              description
              color
              icon
              createdAt
              updatedAt
            }
          }
        }
        """

        response = self._execute_query(query, {"teamId": team_id})

        if not response or "team" not in response or not response["team"] or "parent" not in response["team"] or not \
                response["team"]["parent"]:
            # Cache None to avoid repeated queries for teams without parents
            self._cache_set("parent_by_team", team_id, None)
            return None

        parent_data = response["team"]["parent"]
        parent = LinearTeam(**parent_data)

        # Cache the result
        self._cache_set("parent_by_team", team_id, parent)

        return parent

    def get_triage_responsibility(self, team_id: str) -> TriageResponsibility:
        """
        Get triage responsibility data for a team.

        Args:
            team_id: The ID of the team

        Returns:
            Triage responsibility data
        """
        # Check cache first
        cached_triage = self._cache_get("triage_responsibility_by_team", team_id)
        if cached_triage:
            return cached_triage

        query = """
        query($teamId: String!) {
          team(id: $teamId) {
            triageResponsibility {
              id
              createdAt
              updatedAt
              archivedAt
              action
              timeSchedule {
                createdAt
                entries {
                  startsAt
                  endsAt
                  userId
                }
              }
              currentUser {
                id
                name
                displayName
                email
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"teamId": team_id})

        if not response or "team" not in response or not response["team"] or "triageResponsibility" not in response[
            "team"]:
            return {}

        triage_data = response["team"]["triageResponsibility"]

        if triage_data:
            triage_responsibility = TriageResponsibility(**triage_data)

            # Cache the result
            self._cache_set("triage_responsibility_by_team", team_id, triage_responsibility)

            return triage_responsibility
        return {}

    def _cache_states(self, team_id: str, states: List[LinearState]) -> None:
        """
        Cache states for a team.

        Args:
            team_id: The ID of the team
            states: The list of states to cache
        """
        # Cache the full list of states
        self._cache_set("states_by_team_id", team_id, states)

        # Also cache individual state IDs by name for faster lookups
        for state in states:
            cache_key = f"{team_id}:{state.name}"
            self._cache_set("state_ids_by_name", cache_key, state.id)

    def invalidate_cache(self) -> None:
        """
        Invalidate all team-related caches.
        This should be called after any mutating operations.
        """
        self._cache_clear()
