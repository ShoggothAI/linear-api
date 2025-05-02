# linear-api

A comprehensive Python wrapper for the Linear API with rich Pydantic models, simplified workflows, and an object-oriented design.

## Features

- **Object-Oriented Design**: Clean client-based architecture with dedicated resource managers
- **Pydantic Data Models**: Robust domain objects with complete field sets for Issues, Users, and Projects
- **Simplified API**: Intuitive methods for common Linear operations
- **Metadata Support**: Transparently store and retrieve key-value pairs as attachments to issues
- **Pagination Handling**: Built-in support for paginated API responses
- **Type Safety**: Full type hints and validation through Pydantic
- **Caching**: Efficient caching mechanisms to reduce API calls for frequently used data
- **Issue Management**: Create, read, update, and delete Linear issues with type-safe models
- **Error Handling**: Robust error handling with descriptive error messages

The set of supported data fields and operations is much richer than in other Python wrappers for Linear API such as [linear-py](https://gitlab.com/thinkhuman-public/linear-py) and [linear-python](https://github.com/jpbullalayao/linear-python).

## Installation

```bash
pip install linear-api
```

## Usage Examples

### Basic Client Setup

```python
from linear_api import LinearClient

# Create a client with an API key
client = LinearClient(api_key="your_api_key_here")

# Or use environment variable LINEAR_API_KEY
import os
os.environ["LINEAR_API_KEY"] = "your_api_key_here"
client = LinearClient()  # Will use the environment variable
```

### Complete Workflow Example

```python
from linear_api import (
    LinearClient,
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearPriority
)

# Create a client
client = LinearClient()

# Step 1: Get current user
me = client.users.get_me()
print(f"Current user: {me.name} ({me.email})")

# Step 2: Get all teams
teams = client.teams.get_all()
team_name = next(iter(teams.values())).name

# Step 3: Get all issues for a specific team
team_issues = client.issues.get_by_team(team_name)

# Step 4: Get detailed information about a specific issue
if team_issues:
    # Get the first issue ID from the list
    first_issue_id = next(iter(team_issues.keys()))
    issue = client.issues.get(first_issue_id)
    
    # Step 5: Create a sub-issue under the first issue
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

    new_issue = client.issues.create(sub_issue)
    
    # Step 6: Access metadata that was stored as an attachment
    metadata = new_issue.metadata
    # metadata = {'source': 'api_example', 'automated': True, 'importance_score': 7.5}
    
    # Step 7: Update the issue
    update_data = LinearIssueUpdateInput(
        title="Updated title",
        description="This issue has been updated via the linear-api Python package",
        priority=LinearPriority.HIGH
    )
    updated_issue = client.issues.update(new_issue.id, update_data)
```

### Working with Issues

```python
from linear_api import LinearClient, LinearIssueInput, LinearPriority

client = LinearClient()

# Create a new issue
issue_input = LinearIssueInput(
    title="New Feature Request",
    description="Implement a new feature for the application",
    teamName="Engineering",
    priority=LinearPriority.HIGH
)

new_issue = client.issues.create(issue_input)
print(f"Created issue: {new_issue.title} (ID: {new_issue.id})")

# Get issue details
issue = client.issues.get(new_issue.id)
print(f"Issue state: {issue.state.name}")

# Get issue attachments
attachments = client.issues.get_attachments(issue.id)
print(f"Issue has {len(attachments)} attachments")

# Get issue comments
comments = client.issues.get_comments(issue.id)
print(f"Issue has {len(comments)} comments")

# Delete the issue
client.issues.delete(issue.id)
```

### Working with Projects

```python
from linear_api import LinearClient

client = LinearClient()

# Create a new project
project = client.projects.create(
    name="Q4 Roadmap",
    team_name="Engineering",
    description="Our Q4 development roadmap and milestones"
)
print(f"Created project: {project.name} (ID: {project.id})")

# Get all projects for a team
team_id = client.teams.get_id_by_name("Engineering")
projects = client.projects.get_all(team_id=team_id)
print(f"Found {len(projects)} projects for team 'Engineering'")

# Update a project
updated_project = client.projects.update(
    project.id,
    name="Updated Q4 Roadmap",
    description="Updated description for our Q4 roadmap"
)
print(f"Updated project: {updated_project.name}")

# Delete a project
client.projects.delete(project.id)
```

### Working with Teams

```python
from linear_api import LinearClient

client = LinearClient()

# Get all teams
teams = client.teams.get_all()
print(f"Found {len(teams)} teams:")
for team in teams.values():
    print(f"  - {team.name} (ID: {team.id})")

# Get team by ID
team_id = next(iter(teams.values())).id
team = client.teams.get(team_id)
print(f"Team details: {team.name} (Key: {team.key})")

# Get team ID by name
team_id = client.teams.get_id_by_name("Engineering")
print(f"Team ID: {team_id}")

# Get workflow states for a team
states = client.teams.get_states(team_id)
print(f"Found {len(states)} workflow states for team 'Engineering':")
for state in states:
    print(f"  - {state.name} (Type: {state.type}, Color: {state.color})")
```

### Working with Users

```python
from linear_api import LinearClient

client = LinearClient()

# Get the current user
me = client.users.get_me()
print(f"Current user: {me.name} ({me.email})")

# Get all users
users = client.users.get_all()
print(f"Found {len(users)} users")

# Get a mapping of user IDs to emails
email_map = client.users.get_email_map()
print(f"Email map contains {len(email_map)} entries")

# Get user by ID
user_id = next(iter(users.values())).id
user = client.users.get(user_id)
print(f"User details: {user.name} ({user.email})")

# Get user ID by email
user_id = client.users.get_id_by_email("user@example.com")
print(f"User ID: {user_id}")

# Get user ID by name (fuzzy matching)
user_id = client.users.get_id_by_name("John Doe")
print(f"User ID: {user_id}")
```

## Authentication

Set your Linear API key as an environment variable:

```bash
export LINEAR_API_KEY="your_api_key_here"
```

Or provide it directly when creating the client:

```python
from linear_api import LinearClient

client = LinearClient(api_key="your_api_key_here")
```

## Advanced Usage

### Handling Pagination

The library automatically handles pagination for you behind the scenes. For example, when you call `client.issues.get_all()`, it will automatically fetch all pages of issues.

### Error Handling

The library provides detailed error messages when operations fail. Here's how to handle errors:

```python
from linear_api import LinearClient

client = LinearClient()

try:
    # Try to get a non-existent issue
    issue = client.issues.get("non-existent-id")
except ValueError as e:
    print(f"Error: {e}")
```

## Architecture

The library follows a clean object-oriented architecture:

- `LinearClient`: Main entry point that provides access to all API resources
- Resource Managers:
  - `IssueManager`: Manages issues (creation, retrieval, updates, deletion)
  - `ProjectManager`: Manages projects
  - `TeamManager`: Manages teams and workflow states
  - `UserManager`: Manages users

## License

MIT