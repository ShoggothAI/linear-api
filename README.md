# linear-api

A comprehensive Python wrapper for the Linear API with rich Pydantic models and simplified workflows. 
## Comparison with Other Libraries


## Features

- **Pydantic Data Models**: Robust domain objects with fairly complete field sets for Issues, Users, Teams, Projects, and more
- **Simplified API**: Easy-to-use functions for common Linear operations
- **Metadata Support**: Transparently store and retrieve key-value pairs as attachments to issues
- **Pagination Handling**: Built-in support for paginated API responses
- **Type Safety**: Full type hints and validation through Pydantic

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
    
    # Import domain models
    LinearIssue,
    LinearIssueInput, 
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

## Authentication

Set your Linear API key as an environment variable:

```bash
export LINEAR_API_KEY="your_api_key_here"
```

## License

MIT
