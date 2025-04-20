from enum import StrEnum
from typing import Dict, Optional, Any, Tuple

from linear_api.call_linear_api import call_linear_api


class LinearResourceType(StrEnum):
    """Enum representing different types of Linear resources."""

    TEAM = "team"
    STATE = "state"
    PROJECT = "project"


# Cache for storing resource data
_cache: Dict[Tuple[LinearResourceType, Optional[str]], Dict[str, str]] = {}


def _get_query_for_resource(
    resource_type: LinearResourceType, team_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get the appropriate GraphQL query for a resource type."""
    if resource_type == LinearResourceType.TEAM:
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
        return {"query": query}

    elif resource_type == LinearResourceType.STATE:
        if team_id:
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
            return {"query": query, "variables": {"teamId": team_id}}
        else:
            query = """
            query {
                workflowStates {
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
            return {"query": query}

    elif resource_type == LinearResourceType.PROJECT:
        if team_id:
            query = """
                query GetProjectsByTeam($teamId: String!) {  # Changed from ID! to String!
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
            return {"query": query, "variables": {"teamId": team_id}}
        else:
            query = """
            query {
                projects {
                    nodes {
                        id
                        name
                        description
                    }
                }
            }
            """
            return {"query": query}

    raise ValueError(f"Unknown resource type: {resource_type}")


def _get_resource_data_key(resource_type: LinearResourceType) -> str:
    """Get the key for accessing resource data in the API response."""
    # Map resource types to their API response keys
    resource_keys = {
        LinearResourceType.TEAM: "teams",
        LinearResourceType.STATE: "workflowStates",
        LinearResourceType.PROJECT: "projects",
    }

    if resource_type in resource_keys:
        return resource_keys[resource_type]

    raise ValueError(f"Unknown resource type: {resource_type}")


def _get_resource_name(resource_type: LinearResourceType) -> str:
    """Get the human-readable name of a resource type."""
    # Map resource types to their human-readable names
    resource_names = {
        LinearResourceType.TEAM: "Team",
        LinearResourceType.STATE: "State",
        LinearResourceType.PROJECT: "Project",
    }

    if resource_type in resource_names:
        return resource_names[resource_type]

    raise ValueError(f"Unknown resource type: {resource_type}")


def get_resources(
    resource_type: LinearResourceType, team_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Fetch resources from Linear API.

    Args:
        resource_type: The type of resource to fetch (TEAM, STATE, PROJECT)
        team_id: Optional team ID to filter resources by team (not applicable for TEAM)

    Returns:
        Dictionary mapping resource names to their IDs
    """
    # Get the appropriate query for this resource type
    query_data = _get_query_for_resource(resource_type, team_id)

    # Call the Linear API
    data = call_linear_api(query_data)

    # Extract the resource data from the response
    resource_key = _get_resource_data_key(resource_type)
    if team_id is not None and resource_key == "projects":
        # Workaround for a quirk in Linear API: can't seem to be able to filter projects by team directly
        data = data["team"]

    resources = data[resource_key]["nodes"]

    # Return a dictionary mapping names to IDs
    return {resource["name"]: resource["id"] for resource in resources}


def resource_name_to_id(
    resource_type: LinearResourceType, name: str, team_id: Optional[str] = None
) -> str:
    """
    Convert a resource name to its ID.

    Args:
        resource_type: The type of resource (TEAM, STATE, PROJECT)
        name: The name of the resource
        team_id: Optional team ID to filter resources by team (not applicable for TEAM)

    Returns:
        The ID of the resource

    Raises:
        ValueError: If the resource is not found
    """
    global _cache

    # Create a cache key
    cache_key = (resource_type, team_id)

    # Check if we have this resource type cached
    if cache_key not in _cache:
        # Fetch resources and update cache
        _cache[cache_key] = get_resources(resource_type, team_id)

    # Try to find the resource in the cache
    if name in _cache[cache_key]:
        return _cache[cache_key][name]

    # If not found, refresh the cache and try again
    _cache[cache_key] = get_resources(resource_type, team_id)

    if name in _cache[cache_key]:
        return _cache[cache_key][name]

    # If still not found, raise an error
    resource_name = _get_resource_name(resource_type)
    team_info = f" in team {team_id}" if team_id else ""
    raise ValueError(f"{resource_name} '{name}'{team_info} not found")


# Convenience functions for backward compatibility


def get_teams() -> Dict[str, str]:
    """Get all teams from Linear API."""
    return get_resources(LinearResourceType.TEAM)


def team_name_to_id(team_name: str) -> str:
    """Convert a team name to its ID."""
    return resource_name_to_id(LinearResourceType.TEAM, team_name)


def get_states(team_id: Optional[str] = None) -> Dict[str, str]:
    """Get workflow states from Linear API."""
    return get_resources(LinearResourceType.STATE, team_id)


def state_name_to_id(state_name: str, team_id: Optional[str] = None) -> str:
    """Convert a state name to its ID."""
    return resource_name_to_id(LinearResourceType.STATE, state_name, team_id)


def get_projects(team_id: Optional[str] = None) -> Dict[str, str]:
    """Get projects from Linear API."""
    return get_resources(LinearResourceType.PROJECT, team_id)


def project_name_to_id(project_name: str, team_id: Optional[str] = None) -> str:
    """Convert a project name to its ID."""
    return resource_name_to_id(LinearResourceType.PROJECT, project_name, team_id)


if __name__ == "__main__":
    # Test the functions
    print("Using specific functions:")
    print("\nTeams:")
    test_teams = get_teams()
    print(test_teams)

    print("\nStates:")
    test_states = get_states()
    print(test_states)

    print("\nProjects:")
    test_projects = get_projects()
    print(test_projects)

    print("\n\nUsing generic functions:")
    print("\nTeams:")
    test_teams = get_resources(LinearResourceType.TEAM)
    print(test_teams)

    print("\nStates:")
    test_states = get_resources(LinearResourceType.STATE)
    print(test_states)

    print("\nProjects:")
    test_projects = get_resources(LinearResourceType.PROJECT)
    print(test_projects)

    # Test name to ID conversion
    if test_teams:
        team_name = next(iter(test_teams.keys()))
        team_id = team_name_to_id(team_name)
        print(f"\nTeam '{team_name}' has ID: {team_id}")

        # Test states for this team
        team_states = get_states(team_id)
        if team_states:
            state_name = next(iter(team_states.keys()))
            state_id = state_name_to_id(state_name, team_id)
            print(f"State '{state_name}' in team '{team_name}' has ID: {state_id}")
