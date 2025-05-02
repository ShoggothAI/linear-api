# linear-api

A comprehensive Python wrapper for the Linear API with rich Pydantic models and simplified workflows.

## Features

- **Pydantic Data Models**: Robust domain objects with fairly complete field sets for Issues, Users, and Projects (validated via GraphQL introspection)
- **Simplified API**: Easy-to-use functions for common Linear operations
- **Metadata Support**: Transparently store and retrieve key-value pairs as attachments to issues
- **Pagination Handling**: Built-in support for paginated API responses
- **Type Safety**: Full type hints and validation through Pydantic
- **Issue Management**: Create, read, update, and delete Linear issues with type-safe models

The set of supported data fields and operations is much richer than in other Python wrappers for Linear API s
uch as [linear-py](https://gitlab.com/thinkhuman-public/linear-py) and [linear-python](https://github.com/jpbullalayao/linear-python).


## Installation

```bash
pip install linear-api
```

## Usage Examples

### Complete Workflow Example

```python
import os
from pprint import pprint
from linear_api import (
    # Import functions
    get_team_issues,
    get_linear_issue,
    create_issue,
    update_issue,

    # Import domain models
    LinearIssue,
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearPriority
)

# Set your API key (or set it as an environment variable)
# os.environ["LINEAR_API_KEY"] = "your_api_key_here"

# Step 1: Get all issues for a specific team
team_name = "Engineering"  # Replace with your team name
team_issues = get_team_issues(team_name)

# Step 2: Get detailed information about a specific issue
if team_issues:
    # Get the first issue ID from the list
    first_issue_id = next(iter(team_issues.keys()))
    issue: LinearIssue = get_linear_issue(first_issue_id)


    # Step 4: Create a sub-issue under the first issue
    sub_issue = LinearIssueInput(
        title=f"Sub-task for {issue.title}",
        description="This is a sub-task created via the linear-api Python package",
        teamName=team_name,
        priority=LinearPriority.MEDIUM,
        parentId=first_issue_id,  # Set the parent ID to create a sub-issue
        # Add arbitrary metadata that will be stored as an attachment
        metadata={
            "source": "api_example",
            "automated": True,
            "importance_score": 7.5
        }
    )

    response = create_issue(sub_issue)

    # Step 5: Fetch the newly created issue to verify metadata
    new_issue_id = response["issueCreate"]["issue"]["id"]
    new_issue: LinearIssue = get_linear_issue(new_issue_id)
    # Access metadata that was stored as an attachment
    metadata = new_issue.metadata
    # metadata = {'source': 'api_example', 'automated': True, 'importance_score': 7.5}

    # Step 6: Update the issue
    update_data = LinearIssueUpdateInput(
        title="Updated title",
        description="This issue has been updated via the linear-api Python package",
        priority=LinearPriority.HIGH
    )
    update_response = update_issue(new_issue_id, update_data)
```

### Updating Issues

```python
from linear_api import get_linear_issue, update_issue, LinearIssueUpdateInput, LinearPriority

# Get an existing issue
issue_id = "ISSUE-123"  # Replace with your issue ID
issue = get_linear_issue(issue_id)

# Create an update object with only the fields you want to change
update_data = LinearIssueUpdateInput(
    title="Updated Issue Title",
    description="This issue has been updated with new information",
    priority=LinearPriority.HIGH
)

# Update the issue
response = update_issue(issue_id, update_data)

# Verify the update was successful
if response["issueUpdate"]["success"]:
    print(f"Issue {issue_id} updated successfully")

# You can also update state and project using names instead of IDs
state_update = LinearIssueUpdateInput(
    stateName="In Progress",  # Will be converted to stateId automatically
    projectName="Q3 Goals"    # Will be converted to projectId automatically
)
update_issue(issue_id, state_update)
```

### Working with Users

```python
from linear_api import fetch_linear_user, get_user_email_map

# Get a mapping of all user IDs to emails
user_map = get_user_email_map()
# {'user_id_1': 'user1@example.com', 'user_id_2': 'user2@example.com', ...}

# Fetch detailed information about a specific user
first_user_id = list(user_map.keys())[0]
user = fetch_linear_user(first_user_id, api_key=None)  # Uses env var LINEAR_API_KEY

user_display_name = user.displayName
user_email = user.email
```

### Managing Projects

```python
from linear_api import create_project, get_project, delete_project

# Create a new project in a team
team_name = "Engineering"
project_name = "Q4 Roadmap"
response = create_project(
    name=project_name,
    team_name=team_name,
    description="Our Q4 development roadmap and milestones"
)

# Get the project ID from the response
project_id = response["projectCreate"]["project"]["id"]

# Fetch a project by ID
project = get_project(project_id)
print(f"Project name: {project.name}")
print(f"Project description: {project.description}")

# Delete a project
delete_response = delete_project(project_id)
if delete_response["projectDelete"]["success"]:
    print(f"Project '{project_name}' deleted successfully")
```

## Authentication

Set your Linear API key as an environment variable:

```bash
export LINEAR_API_KEY="your_api_key_here"
```

## License

MIT
