"""
Example usage of the automatic connection unwrapping feature.

This script demonstrates how to use the connection unwrapping functionality
to simplify working with paginated GraphQL responses.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from linear_api.client import LinearClient



def example_with_manual_pagination():
    """Example using the traditional manual pagination approach."""
    client = LinearClient()

    # Disable automatic connection unwrapping to demonstrate the difference
    client.disable_connection_unwrapping()

    print("=== Manual Pagination Example ===")

    # Need to use _handle_pagination to get all projects
    query = """
    query GetAllProjects($cursor: String) {
        projects(first: 10, after: $cursor) {
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

    # Manually handle pagination
    project_nodes = client.teams._handle_pagination(
        query,
        {},
        ["projects", "nodes"]
    )

    print(f"Retrieved {len(project_nodes)} projects with manual pagination")

    # To get all issues for each project, we'd need another pagination loop
    all_issues = {}
    for project in project_nodes:
        project_id = project["id"]
        project_issues = client.issues.get_by_project(project_id)
        all_issues[project_id] = project_issues

    print(f"Retrieved issues for {len(all_issues)} projects")

    # Return to default setting
    client.enable_connection_unwrapping()


def example_with_auto_unwrapping():
    """Example using the new automatic connection unwrapping."""
    client = LinearClient()

    # Ensure automatic connection unwrapping is enabled (default)
    client.enable_connection_unwrapping()

    print("=== Automatic Connection Unwrapping Example ===")

    # Simple query that uses connections at multiple levels
    query = """
    query {
        projects(first: 10) {
            nodes {
                id
                name
                issues(first: 10) {
                    nodes {
                        id
                        title
                        labels {
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

    # Execute the query once - all connections will be unwrapped automatically
    result = client.teams._execute_query(query)

    # Access all projects
    projects = result.get("projects", {}).get("nodes", [])

    # Count projects and issues
    project_count = len(projects)
    issue_count = sum(len(project.get("issues", {}).get("nodes", [])) for project in projects)

    print(f"Retrieved {project_count} projects with all their issues in a single query")
    print(f"Total issues retrieved: {issue_count}")

    # The results include all pages from all connections automatically


def main():
    """Run the examples."""
    # Set the API key from environment variable
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("ERROR: LINEAR_API_KEY environment variable not set")
        return

    # Run both examples for comparison
    example_with_manual_pagination()
    print("\n")
    example_with_auto_unwrapping()


if __name__ == "__main__":
    main()