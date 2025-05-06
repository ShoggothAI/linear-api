# linear-api

A comprehensive Python wrapper for the Linear API with rich Pydantic models, simplified workflows, and an object-oriented design.

## Features

- **Object-Oriented Design**: Clean client-based architecture with dedicated resource managers
- **Pydantic Data Models**: Robust domain objects with complete field sets for Issues, Users, and Projects
- **Simplified API**: Intuitive methods for common Linear operations
- **Metadata Support**: Transparently store and retrieve key-value pairs as attachments to issues
- **Automatic Pagination**: Built-in handling of GraphQL connections with automatic unwrapping
- **Type Safety**: Full type hints and validation through Pydantic
- **Centralized Caching**: Configurable caching system to reduce API calls for frequently used data
- **Issue Management**: Create, read, update, and delete Linear issues with type-safe models
- **Error Handling**: Robust error handling with descriptive error messages
- **GraphQL Type Integration**: Domain models are aware of their corresponding GraphQL types

The set of supported data fields and operations is much richer than in other Python wrappers for Linear API such as [linear-py](https://gitlab.com/thinkhuman-public/linear-py) and [linear-python](https://github.com/jpbullalayao/linear-python).

## Installation

```bash
pip install linear-api
```

## Usage Examples

### Basic Client Setup

```python
from linear_api import LinearClient

# Create a client with default settings
client = LinearClient(api_key="your_api_key_here")

# Or use environment variable LINEAR_API_KEY
import os
os.environ["LINEAR_API_KEY"] = "your_api_key_here"
client = LinearClient()  # Will use the environment variable

# Configure with all available options
client = LinearClient(
    api_key="your_api_key_here",
    
    # Caching options
    enable_cache=True,       # Enable/disable caching (default: True)
    cache_ttl=3600,          # Cache time-to-live in seconds (default: 3600 - 1 hour)
    
    # Connection unwrapping options
    auto_unwrap_connections=True  # Automatically handle GraphQL connection pagination (default: True)
)

# You can also configure these settings after creating the client

# Control caching
client.cache.disable()  # Disable caching
client.cache.enable()   # Enable caching
client.clear_cache()    # Clear all caches

# Control connection unwrapping
client.disable_connection_unwrapping()  # Disable automatic connection unwrapping
client.enable_connection_unwrapping()   # Enable automatic connection unwrapping
```

The `auto_unwrap_connections` parameter controls whether the client automatically handles GraphQL connection patterns and pagination. 
When enabled (default), the client will automatically make additional API calls to fetch all pages of data when it encounters a 
GraphQL connection pattern in the response. This makes working with large datasets much easier as you don't need to manually handle pagination.

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

## Working with Deleted Items

Linear API uses a "soft delete" approach where objects (issues, projects, and other entities) are not physically removed from the database. Instead, they are marked with a `trashed` flag to indicate they're in the "trash bin".

When you call a `delete()` method for an issue or project:
```python
# Delete (move to trash) an issue
client.issues.delete(issue_id)

# Delete (move to trash) a project
client.projects.delete(project_id)
```

The object is not physically deleted, but marked as `trashed=True` and an `archivedAt` attribute is set with the time when the object was placed in the trash bin.

This allows for recovery of objects from the trash if needed through the Linear interface. When developing with the API, it's important to understand that deleted objects are still accessible through the API and can be retrieved via `get()`, `get_all()`, and other methods.

To programmatically check if an object is in the trash bin, you can use the following approach:

```python
# Check object status
issue = client.issues.get(issue_id)
if issue.trashed:
    print("Issue is in the trash bin")
    print(f"Deletion time: {issue.archivedAt}")
else:
    print("Issue is active")
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

### Centralized Caching

The library provides a powerful centralized caching system to improve performance:

```python
from linear_api import LinearClient

# Create a client with caching options
client = LinearClient(
    enable_cache=True,  # Enable caching (default)
    cache_ttl=1800      # Set Time-To-Live to 30 minutes (default is 1 hour)
)

# Disable caching dynamically
client.cache.disable()

# Re-enable caching
client.cache.enable()

# Clear all caches
client.clear_cache()

# Clear a specific cache (using the full cache name)
client.clear_cache("User_users_by_id")

# Get cache statistics
stats = client.cache.stats
print(f"Cache hit count: {stats['hit_count']}")
print(f"Cache miss count: {stats['miss_count']}")
print(f"Cache hit rate: {stats['hit_rate'] * 100:.1f}%")
print(f"Number of caches: {stats['cache_count']}")
print(f"Total entries: {client.cache.get_cache_size()}")
```

The caching system automatically caches:
- Individual resources (issues, users, teams, projects)
- Collection responses (all issues, all teams, etc.)
- ID lookup results (get_id_by_name, get_id_by_email)
- Other frequently used data

Cache entries are automatically invalidated when related resources are modified (create, update, delete).

### Automatic Connection Unwrapping

Linear API, like many GraphQL APIs, uses a pattern called "Connections" for paginated results. These connections typically have this structure:

```json
{
  "nodes": [...],  // The actual items on the current page
  "pageInfo": {
    "hasNextPage": true,  // Whether there are more pages
    "endCursor": "cursor-value"  // Used to fetch the next page
  }
}
```

Traditionally, clients need to manually handle pagination by making multiple API calls and combining results. However, this library provides automatic connection unwrapping that handles this complexity for you:

```python
from linear_api import LinearClient

# Create a client with unwrapping enabled (default)
client = LinearClient(auto_unwrap_connections=True)

# This query will automatically fetch ALL pages of results
# even if there are hundreds of items spread across multiple pages
query = """
query {
  projects {
    nodes {
      id
      name
      issues {
        nodes {
          id
          title
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

# Access all projects and their issues without worrying about pagination
projects = result.get("projects", {}).get("nodes", [])
for project in projects:
    issues = project.get("issues", {}).get("nodes", [])
    print(f"Project {project['name']} has {len(issues)} issues")

# You can disable this behavior if you prefer to handle pagination manually
client.disable_connection_unwrapping()

# Re-enable it later
client.enable_connection_unwrapping()
```

Key features of automatic connection unwrapping:

1. **Nested Connections**: Handles connections at any level in the response
2. **Transparent**: Works with existing queries without modification
3. **Efficiency**: Makes the minimum number of API calls necessary
4. **Configurable**: Can be enabled/disabled globally or per manager
5. **Cursor Management**: Automatically handles cursor-based pagination

Note that while this feature is extremely convenient, it may increase the number of API calls for large datasets. If you're concerned about rate limits or performance, you can disable this feature and implement manual pagination using the `_handle_pagination` method.

### GraphQL Type Information

Domain models now know their corresponding GraphQL types through the `linear_class_name` property:

```python
from linear_api import LinearIssue, LinearTeam, LinearUser

# Access GraphQL type names statically
print(f"Issue GraphQL type: {LinearIssue.linear_class_name}")  # "Issue"
print(f"Team GraphQL type: {LinearTeam.linear_class_name}")    # "Team"
print(f"User GraphQL type: {LinearUser.linear_class_name}")    # "User"

# Access from an instance
issue = client.issues.get(issue_id)
print(f"Issue {issue.id} type: {issue.get_linear_class_name()}")  # "Issue"

# Use for dynamic query building
type_name = LinearIssue.linear_class_name
query = f"""
query Get{type_name}($id: String!) {{
  {type_name.lower()}(id: $id) {{
    id
    title
  }}
}}
"""
```

This feature makes it easier to:
- Build dynamic GraphQL queries
- Validate domain models against the API schema
- Understand the relationship between your code and the Linear API

### Handling Pagination Manually

While automatic connection unwrapping is recommended for most cases, you can still use the manual pagination approach:

```python
from linear_api import LinearClient

client = LinearClient()

# Disable automatic unwrapping for this example
client.disable_connection_unwrapping()

# Use the pagination handler directly
query = """
query GetProjects($cursor: String) {
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

projects = client.projects._handle_pagination(
    query,
    {},
    ["projects", "nodes"]
)

print(f"Found {len(projects)} projects")
```

The `_handle_pagination` method handles:
- Executing the initial query
- Checking for more pages
- Making additional requests with the correct cursor
- Combining results from all pages

### Error Handling

The library provides detailed error messages when operations fail:

```python
from linear_api import LinearClient

client = LinearClient()

try:
    # Try to get a non-existent issue
    issue = client.issues.get("non-existent-id")
except ValueError as e:
    print(f"Error: {e}")  # Error: Issue with ID non-existent-id not found

try:
    # Try to create an issue with missing required fields
    client.issues.create({"title": "Missing team name"})
except Exception as e:
    print(f"Creation error: {e}")
```

## Architecture

The library follows a clean object-oriented architecture:

- `LinearClient`: Main entry point that provides access to all API resources and configuration
- Resource Managers:
  - `IssueManager`: Manages issues (creation, retrieval, updates, deletion)
  - `ProjectManager`: Manages projects
  - `TeamManager`: Manages teams and workflow states
  - `UserManager`: Manages users
- Support Services:
  - `CacheManager`: Centralized caching system
  - `ConnectionUnwrapper`: Automatic handling of GraphQL connections
- Domain Models:
  - All models inherit from `LinearModel` with GraphQL type awareness
  - Organized in logical modules for better maintainability

## License

MIT