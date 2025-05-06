"""
Basic usage examples for the Linear API client.

This module demonstrates the basic usage of the Linear API client.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from linear_api import (
    LinearClient,
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearPriority,
)


def main():
    """Run the example code."""
    # Create a client instance
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("ERROR: Please set the LINEAR_API_KEY environment variable.")
        return

    client = LinearClient(api_key=api_key)
    print("Linear API client initialized.")

    # Example 1: Get current user
    try:
        me = client.users.get_me()
        print(f"\nCurrent user: {me.name} ({me.email})")
    except Exception as e:
        print(f"Error getting current user: {e}")

    # Example 2: Get all teams
    try:
        teams = client.teams.get_all()
        print(f"\nFound {len(teams)} teams:")
        for team in teams.values():
            print(f"  - {team.name} (ID: {team.id})")

        # Select the first team for further examples
        team = next(iter(teams.values()))
    except Exception as e:
        print(f"Error getting teams: {e}")
        return

    # Example 3: Get workflow states for a team
    try:
        states = client.teams.get_states(team.id)
        print(f"\nFound {len(states)} workflow states for team '{team.name}':")
        for state in states:
            print(f"  - {state.name} (Type: {state.type}, Color: {state.color})")

        # Select a "todo" state for creating an issue
        todo_state = next((s for s in states if s.type.lower() == "unstarted"), states[0])
    except Exception as e:
        print(f"Error getting workflow states: {e}")
        return

    # Example 4: Get all projects for a team
    try:
        projects = client.projects.get_all(team.id)
        print(f"\nFound {len(projects)} projects for team '{team.name}':")
        for project in projects.values():
            print(f"  - {project.name} (ID: {project.id})")

        # Create a new project if none exist
        if not projects:
            print("\nNo projects found. Creating a new project...")
            new_project = client.projects.create(
                name="Example Project",
                team_name=team.name,
                description="A project created by the Linear API client example.",
            )
            print(f"Created project: {new_project.name} (ID: {new_project.id})")
            selected_project = new_project
        else:
            selected_project = next(iter(projects.values()))
    except Exception as e:
        print(f"Error working with projects: {e}")
        return

    # Example 5: Create a new issue
    try:
        print(f"\nCreating a new issue in team '{team.name}'...")
        issue_input = LinearIssueInput(
            title="Example Issue",
            teamName=team.name,
            description="This is an example issue created by the Linear API client.",
            priority=LinearPriority.MEDIUM,
            stateName=todo_state.name,
            projectName=selected_project.name,
            dueDate=datetime.now(),
            metadata={
                "example": "value",
                "created_by": "linear_api_example",
            },
        )

        new_issue = client.issues.create(issue_input)
        print(f"Created issue: {new_issue.title} (ID: {new_issue.id})")

        # Example 6: Update the issue
        print(f"\nUpdating issue {new_issue.title}...")
        update_data = LinearIssueUpdateInput(
            title="Updated Example Issue",
            description="This issue was updated by the Linear API client.",
            priority=LinearPriority.HIGH,
        )

        updated_issue = client.issues.update(new_issue.id, update_data)
        print(f"Updated issue: {updated_issue.title} (Priority: {updated_issue.priority.name})")

        # Example 7: Get issue attachments
        attachments = client.issues.get_attachments(updated_issue.id)
        print(f"\nIssue has {len(attachments)} attachments")

        # Example 8: Delete the issue
        if input("\nDelete the created issue? (y/n): ").lower() == 'y':
            client.issues.delete(updated_issue.id)
            print(f"Deleted issue: {updated_issue.title}")
    except Exception as e:
        print(f"Error working with issues: {e}")

    print("\nExample completed.")


if __name__ == "__main__":
    main()