from functools import lru_cache


from linearpy.call_linear_api import call_linear_api

def get_teams():
    # Define the GraphQL query to fetch teams
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
    data = call_linear_api({"query": query})
    teams = data["teams"]["nodes"]
    return {team['name']: team['id'] for team in teams}

# Cache the result of get_teams
teams = get_teams()

def team_name_to_id(team_name: str):
    global teams
    if team_name in teams:
        return teams[team_name]
    else:
        teams = get_teams()  # Update the global teams variable
        if team_name in teams:
            return teams[team_name]
        else:
            raise ValueError(f"Team {team_name} not found")

if __name__ == "__main__":
    test = get_teams()
    print(test)