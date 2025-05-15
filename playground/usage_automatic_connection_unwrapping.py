"""
Comprehensive example to get all projects, teams, and their issues using built-in methods.

This script demonstrates how to use the existing methods in the LinearClient to retrieve
all issues from all projects and teams.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from linear_api.client import LinearClient


def get_all_data():
    """
    Get all projects, teams, and their issues using the built-in methods.

    Returns:
        Dictionaries of projects, teams, and their issues
    """
    client = LinearClient()

    print("=== Retrieving All Data Using Built-in Methods ===")

    # --- PROJECTS SECTION ---
    print("\n--- PROJECTS ---")

    # Get all projects
    print("Fetching all projects...")
    all_projects = client.projects.get_all()
    print(f"Retrieved {len(all_projects)} projects")

    # Get all issues for each project
    total_project_issues = 0
    all_issues_by_project = {}

    for index, (project_id, project) in enumerate(all_projects.items()):
        print(f"Fetching issues for project {index + 1}/{len(all_projects)}: {project.name}")

        # Use the built-in method to get all issues for a project
        project_issues = client.issues.get_by_project(project_id)
        all_issues_by_project[project_id] = project_issues
        total_project_issues += len(project_issues)

        print(f"  - Found {len(project_issues)} issues")

    # --- TEAMS SECTION ---
    print("\n--- TEAMS ---")

    # Get all teams
    print("Fetching all teams...")
    all_teams = client.teams.get_all()
    print(f"Retrieved {len(all_teams)} teams")

    # Get all issues for each team
    total_team_issues = 0
    all_issues_by_team = {}

    for index, (team_id, team) in enumerate(all_teams.items()):
        print(f"Fetching issues for team {index + 1}/{len(all_teams)}: {team.name}")

        # Get issues for the team using the team name
        team_issues = client.issues.get_by_team(team.name)
        all_issues_by_team[team_id] = team_issues
        total_team_issues += len(team_issues)

        print(f"  - Found {len(team_issues)} issues")

        # Optionally, get team members
        team_members = client.teams.get_members(team_id)
        print(f"  - Team has {len(team_members)} members")

        # Optionally, get team states
        team_states = client.teams.get_states(team_id)
        print(f"  - Team has {len(team_states)} workflow states")

    # --- SUMMARY ---
    print("\n=== SUMMARY ===")
    print(f"Total projects: {len(all_projects)}")
    print(f"Total teams: {len(all_teams)}")
    print(f"Total issues in projects: {total_project_issues}")
    print(f"Total issues in teams: {total_team_issues}")

    # Print issue count per project
    print("\nIssues per project:")
    for project_id, project in all_projects.items():
        issue_count = len(all_issues_by_project.get(project_id, {}))
        print(f"  - {project.name}: {issue_count} issues")

    # Print issue count per team
    print("\nIssues per team:")
    for team_id, team in all_teams.items():
        issue_count = len(all_issues_by_team.get(team_id, {}))
        print(f"  - {team.name}: {issue_count} issues")

    return {
        "projects": all_projects,
        "project_issues": all_issues_by_project,
        "teams": all_teams,
        "team_issues": all_issues_by_team
    }


def advanced_features_example():
    """
    Demonstrates some advanced features of the API client.
    """
    client = LinearClient()

    print("\n=== ADVANCED FEATURES ===")

    # Get a specific team by name
    print("\nLooking up a specific team...")
    try:
        # Get all teams first to see what's available
        all_teams = client.teams.get_all()
        if all_teams:
            # Use the first team for demonstration
            first_team_name = next(iter(all_teams.values())).name
            team_id = client.teams.get_id_by_name(first_team_name)
            team = client.teams.get(team_id)
            print(f"Found team: {team.name} (ID: {team.id})")

            # Get team's active cycle
            active_cycle = client.teams.get_active_cycle(team.id)
            if active_cycle:
                print(f"  - Active cycle: {active_cycle.get('name', 'unnamed')} (#{active_cycle.get('number', 'N/A')})")
            else:
                print("  - No active cycle")

            # Get team's labels
            team_labels = client.teams.get_labels(team.id)
            print(f"  - Team has {len(team_labels)} labels")
        else:
            print("No teams found")
    except Exception as e:
        print(f"Error looking up team: {e}")

    # Get a specific user
    print("\nLooking up the current user...")
    try:
        current_user = client.users.get_me()
        print(f"Current user: {current_user.displayName} ({current_user.email})")

        # Get assigned issues
        assigned_issues = client.users.get_assigned_issues(current_user.id)
        print(f"  - You have {len(assigned_issues)} assigned issues")
    except Exception as e:
        print(f"Error looking up user: {e}")


def main():
    """Run the examples."""
    # Set the API key from environment variable
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("ERROR: LINEAR_API_KEY environment variable not set")
        return

    # Get all data
    data = get_all_data()

    # Show advanced features
    advanced_features_example()

    # Return data for potential further usage
    return data


if __name__ == "__main__":
    main()