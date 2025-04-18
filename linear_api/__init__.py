__version__ = "0.1.0"

# Domain models
from .domain import (
    LinearIssueInput,
    LinearPriority,
    LinearAttachmentInput,
    LinearIssue,
    LinearUser,
    LinearState,
    LinearLabel,
    LinearProject,
    LinearTeam,
    LinearAttachment
)

# Issue manipulation functions
from .issue_manipulation import (
    create_issue,
    get_linear_issue,
    get_team_issues,
    delete_issue,
    create_attachment
)

# User-related functions
from .get_user import (
    fetch_linear_user,
    get_user_email_map
)

# Resource-related functions
from .get_resources import (
    get_resources,
    resource_name_to_id,
    team_name_to_id,
    state_name_to_id,
    project_name_to_id
)