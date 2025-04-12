import pytest
from linearpy.get_resources import (
    LinearResourceType,
    get_resources,
    resource_name_to_id,
    _get_resource_data_key,
    _get_resource_name,
    _get_query_for_resource
)


class TestLinearResourceType:
    """Tests for the LinearResourceType StrEnum."""

    def test_enum_values(self):
        """Test that the enum values are strings and have the expected values."""
        # Check that the enum values are strings
        assert isinstance(LinearResourceType.TEAM, str)
        assert isinstance(LinearResourceType.STATE, str)
        assert isinstance(LinearResourceType.PROJECT, str)

        # Check the specific string values
        assert LinearResourceType.TEAM == "team"
        assert LinearResourceType.STATE == "state"
        assert LinearResourceType.PROJECT == "project"

    def test_enum_comparison(self):
        """Test that enum values can be compared with strings."""
        # Direct string comparison should work
        assert LinearResourceType.TEAM == "team"
        assert "team" == LinearResourceType.TEAM

        # String methods should work
        assert LinearResourceType.TEAM.upper() == "TEAM"
        assert LinearResourceType.TEAM.capitalize() == "Team"

        # Enum values should be usable as dictionary keys
        test_dict = {
            LinearResourceType.TEAM: "Teams data",
            LinearResourceType.STATE: "States data",
            LinearResourceType.PROJECT: "Projects data"
        }

        assert test_dict[LinearResourceType.TEAM] == "Teams data"
        assert test_dict["team"] == "Teams data"  # String key should work too

    def test_enum_in_functions(self):
        """Test that the enum values work correctly in helper functions."""
        # Test _get_resource_data_key
        assert _get_resource_data_key(LinearResourceType.TEAM) == "teams"
        assert _get_resource_data_key(LinearResourceType.STATE) == "workflowStates"
        assert _get_resource_data_key(LinearResourceType.PROJECT) == "projects"

        # Test _get_resource_name
        assert _get_resource_name(LinearResourceType.TEAM) == "Team"
        assert _get_resource_name(LinearResourceType.STATE) == "State"
        assert _get_resource_name(LinearResourceType.PROJECT) == "Project"

        # Test that invalid resource types raise ValueError
        with pytest.raises(ValueError):
            _get_resource_data_key("invalid_type")

        with pytest.raises(ValueError):
            _get_resource_name("invalid_type")

    def test_get_query_for_resource(self):
        """Test that _get_query_for_resource returns the correct query structure."""
        # Test team query
        team_query = _get_query_for_resource(LinearResourceType.TEAM)
        assert isinstance(team_query, dict)
        assert "query" in team_query
        assert "teams" in team_query["query"]

        # Test state query without team_id
        state_query = _get_query_for_resource(LinearResourceType.STATE)
        assert isinstance(state_query, dict)
        assert "query" in state_query
        assert "workflowStates" in state_query["query"]
        assert "variables" not in state_query

        # Test state query with team_id
        team_id = "team123"
        state_query_with_team = _get_query_for_resource(LinearResourceType.STATE, team_id)
        assert isinstance(state_query_with_team, dict)
        assert "query" in state_query_with_team
        assert "variables" in state_query_with_team
        assert state_query_with_team["variables"]["teamId"] == team_id

        # Test project query without team_id
        project_query = _get_query_for_resource(LinearResourceType.PROJECT)
        assert isinstance(project_query, dict)
        assert "query" in project_query
        assert "projects" in project_query["query"]
        assert "variables" not in project_query

        # Test project query with team_id
        project_query_with_team = _get_query_for_resource(LinearResourceType.PROJECT, team_id)
        assert isinstance(project_query_with_team, dict)
        assert "query" in project_query_with_team
        assert "variables" in project_query_with_team
        assert project_query_with_team["variables"]["teamId"] == team_id

        # Test invalid resource type
        with pytest.raises(ValueError):
            _get_query_for_resource("invalid_type")


class TestResourceCache:
    """Tests for the resource caching mechanism."""

    def test_cache_key_creation(self):
        """Test that cache keys are created correctly by observing cache behavior."""
        # Clear any existing cache from previous tests
        from linearpy.get_resources import _cache
        _cache.clear()

        # Get teams to populate the cache
        teams = get_resources(LinearResourceType.TEAM)
        if not teams:
            pytest.skip("No teams available for testing")

        # Pick a team name that exists
        team_name = next(iter(teams.keys()))

        # First call should add to cache
        team_id_1 = resource_name_to_id(LinearResourceType.TEAM, team_name)

        # Get the cache key for teams
        team_cache_key = (LinearResourceType.TEAM, None)

        # Verify the cache contains the team data
        assert team_cache_key in _cache
        assert team_name in _cache[team_cache_key]
        assert _cache[team_cache_key][team_name] == team_id_1

        # Get states to populate the cache
        states = get_resources(LinearResourceType.STATE)
        if states:
            state_name = next(iter(states.keys()))

            # This should add to cache with a different key
            state_id = resource_name_to_id(LinearResourceType.STATE, state_name)

            # Get the cache key for states
            state_cache_key = (LinearResourceType.STATE, None)

            # Verify the cache contains the state data
            assert state_cache_key in _cache
            assert state_name in _cache[state_cache_key]
            assert _cache[state_cache_key][state_name] == state_id

    def test_cache_hit(self):
        """Test that the cache is used when available by measuring response time."""
        # Clear any existing cache
        from linearpy.get_resources import _cache
        _cache.clear()

        # Get teams to work with
        teams = get_resources(LinearResourceType.TEAM)
        if not teams:
            pytest.skip("No teams available for testing")

        # Pick a team name that exists
        team_name = next(iter(teams.keys()))

        # First call should add to cache
        import time
        start_time = time.time()
        team_id_1 = resource_name_to_id(LinearResourceType.TEAM, team_name)
        first_call_time = time.time() - start_time

        # Second call should use cache and be faster
        start_time = time.time()
        team_id_2 = resource_name_to_id(LinearResourceType.TEAM, team_name)
        second_call_time = time.time() - start_time

        # Verify both calls returned the same ID
        assert team_id_1 == team_id_2

        # The second call should be significantly faster if using cache
        # but we won't assert on exact timing as it can vary
        print(f"First call time: {first_call_time:.6f}s, Second call time: {second_call_time:.6f}s")

    def test_cache_refresh_on_miss(self):
        """Test that the cache is refreshed when a resource is not found."""
        # Clear any existing cache
        from linearpy.get_resources import _cache
        import time
        _cache.clear()

        # Get teams to work with
        teams = get_resources(LinearResourceType.TEAM)
        if not teams:
            pytest.skip("No teams available for testing")

        # Try to get a non-existent team
        non_existent_team = "NonExistentTeam_" + str(int(time.time()))

        # This should fail and try to refresh the cache
        with pytest.raises(ValueError):
            resource_name_to_id(LinearResourceType.TEAM, non_existent_team)

        # Verify the cache contains team data despite the failure
        team_cache_key = (LinearResourceType.TEAM, None)
        assert team_cache_key in _cache
        assert len(_cache[team_cache_key]) > 0


class TestIntegration:
    """Integration tests for the resource functions with the actual API."""

    def test_get_resources_integration(self):
        """Test that get_resources returns data from the API."""
        # This test will make actual API calls
        teams = get_resources(LinearResourceType.TEAM)

        # Basic validation of the response
        assert isinstance(teams, dict)

        # Skip further tests if no teams are available
        if not teams:
            pytest.skip("No teams available for testing")

        # Get a team ID for testing states and projects
        team_id = next(iter(teams.values()))

        # Test getting states
        states = get_resources(LinearResourceType.STATE, team_id)
        assert isinstance(states, dict)

        # Test getting projects
        projects = get_resources(LinearResourceType.PROJECT, team_id)
        assert isinstance(projects, dict)

        # Verify the structure of the returned data
        for name, id in teams.items():
            assert isinstance(name, str)
            assert isinstance(id, str)
            assert len(id) > 0

    def test_resource_name_to_id_integration(self):
        """Test that resource_name_to_id correctly converts names to IDs."""
        # Get all teams
        teams = get_resources(LinearResourceType.TEAM)
        if not teams:
            pytest.skip("No teams available for testing")

        # Pick the first team
        team_name = next(iter(teams.keys()))
        team_id = teams[team_name]

        # Test converting team name to ID
        result = resource_name_to_id(LinearResourceType.TEAM, team_name)
        assert result == team_id

        # Test with a non-existent team
        with pytest.raises(ValueError):
            resource_name_to_id(LinearResourceType.TEAM, "NonExistentTeam")

    def test_cross_resource_integration(self):
        """Test interactions between different resource types."""
        # Get all teams
        teams = get_resources(LinearResourceType.TEAM)
        if not teams:
            pytest.skip("No teams available for testing")

        # Pick the first team
        team_name = next(iter(teams.keys()))
        team_id = teams[team_name]

        # Get states for this team
        states = get_resources(LinearResourceType.STATE, team_id)
        if not states:
            pytest.skip("No states available for testing")

        # Pick a state
        state_name = next(iter(states.keys()))
        state_id = states[state_name]

        # Verify we can get the state ID using the team ID
        result = resource_name_to_id(LinearResourceType.STATE, state_name, team_id)
        assert result == state_id

        # Get projects for this team
        projects = get_resources(LinearResourceType.PROJECT, team_id)

        # If projects exist, test project name to ID conversion
        if projects:
            project_name = next(iter(projects.keys()))
            project_id = projects[project_name]

            result = resource_name_to_id(LinearResourceType.PROJECT, project_name, team_id)
            assert result == project_id

    def test_call_linear_api_directly(self):
        """Test calling the Linear API directly with a GraphQL query."""
        from linearpy.call_linear_api import call_linear_api

        # Simple query to get teams
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

        # Call the API directly
        response = call_linear_api({"query": query})

        # Verify the response structure
        assert "teams" in response
        assert "nodes" in response["teams"]
        assert isinstance(response["teams"]["nodes"], list)

        # If teams exist, verify their structure
        if response["teams"]["nodes"]:
            team = response["teams"]["nodes"][0]
            assert "id" in team
            assert "name" in team
