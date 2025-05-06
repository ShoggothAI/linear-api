"""
Team manager for Linear API.

This module provides the TeamManager class for working with Linear teams and team-related resources.
"""

from typing import Dict, List

from .base_manager import BaseManager
from ..domain import LinearTeam, LinearState


class TeamManager(BaseManager[LinearTeam]):
    """
    Manager for working with Linear teams.

    This class provides methods for retrieving teams and team-related resources
    like workflow states.
    """

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

        # Use a simplified query with basic fields
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
                states {
                    nodes {
                        id
                        name
                        color
                        type
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

        # Extract the states for separate access
        states = []
        if "states" in team_data and "nodes" in team_data["states"]:
            for state in team_data["states"]["nodes"]:
                states.append(LinearState(**state))

        # Remove connection fields from team_data before creating the team object
        if "states" in team_data:
            del team_data["states"]

        # Create the team object
        team = LinearTeam(**team_data)

        # Cache the team
        self._cache_set("teams_by_id", team_id, team)

        # Cache states for this team
        self._cache_states(team_id, states)

        return team

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

        teams = {}
        for team_data in response["teams"]["nodes"]:
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

        for team in response["teams"]["nodes"]:
            if "name" in team and "id" in team:
                # Cache all mappings for future use
                self._cache_set("team_ids_by_name", team["name"], team["id"])

        # Check cache again after populating it
        cached_id = self._cache_get("team_ids_by_name", team_name)
        if cached_id:
            return cached_id

        raise ValueError(f"Team '{team_name}' not found")

    def get_states(self, team_id: str) -> List[LinearState]:
        """
        Get all workflow states for a team.

        Args:
            team_id: The ID of the team

        Returns:
            A list of LinearState objects
        """
        # Check cache first
        cached_states = self._cache_get("states_by_team_id", team_id)
        if cached_states:
            return cached_states

        query = """
        query GetStates($teamId: ID!) {
            workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                nodes {
                    id
                    name
                    color
                    type
                    team {
                        id
                        name
                    }
                }
            }
        }
        """

        response = self._execute_query(query, {"teamId": team_id})

        if not response or "workflowStates" not in response or "nodes" not in response["workflowStates"]:
            return []

        states = []
        for state_data in response["workflowStates"]["nodes"]:
            states.append(LinearState(**state_data))

        # Cache the states
        self._cache_states(team_id, states)

        return states

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
