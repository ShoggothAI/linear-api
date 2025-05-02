from typing import Optional, Dict, Any
import json

from datetime import datetime

from linear_api.call_linear_api import call_linear_api
from linear_api.domain import (
    LinearAttachment,
    LinearIssue,
    LinearLabel,
    LinearState,
    LinearUser,
    LinearProject,
    LinearTeam,
    LinearPriority,
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearAttachmentInput,
    IntegrationService,
    SLADayCountType,
    ActorBot,
    Favorite,
    Comment,
    Cycle,
    ProjectMilestone,
    Template,
    ExternalUser,
    DocumentContent,
)
from linear_api.get_resources import team_name_to_id, state_name_to_id
from linear_api.project_manipulation import project_name_to_id


def create_issue(issue: LinearIssueInput):
    """
    Create a new issue in Linear using the LinearIssueInput model.

    If a parentId is provided, the issue will be created first and then linked to its parent.

    Args:
        issue: The issue data to create

    Returns:
        The response from the Linear API

    Raises:
        ValueError: If teamName, stateName, or projectName doesn't exist
    """
    # Store parent ID if it exists, then remove it for initial creation
    parent_id = None
    if issue.parentId is not None:
        parent_id = issue.parentId
        # We'll set the parent relationship after creating the issue

    # Convert teamName to teamId
    team_id = team_name_to_id(issue.teamName)

    # GraphQL mutation to create an issue
    create_issue_mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        issue {
          id
          title
        }
      }
    }
    """

    # Build the input variables dynamically based on what's set in the issue
    input_vars = {
        "title": issue.title,
        "teamId": team_id,
    }

    # Add optional fields if they are set
    if issue.description is not None:
        input_vars["description"] = issue.description

    # Handle priority as an enum value
    if issue.priority is not None:
        # Convert enum to its integer value
        input_vars["priority"] = issue.priority.value

    # Convert stateName to stateId if provided
    if issue.stateName is not None:
        state_id = state_name_to_id(issue.stateName, team_id)
        input_vars["stateId"] = state_id

    if issue.assigneeId is not None:
        input_vars["assigneeId"] = issue.assigneeId

    # Convert projectName to projectId if provided
    if issue.projectName is not None:
        project_id = project_name_to_id(issue.projectName, team_id)
        input_vars["projectId"] = project_id

    if issue.labelIds is not None and len(issue.labelIds) > 0:
        input_vars["labelIds"] = issue.labelIds

    if issue.dueDate is not None:
        # Format datetime as ISO string
        input_vars["dueDate"] = issue.dueDate.isoformat()

    if issue.estimate is not None:
        input_vars["estimate"] = issue.estimate

    # Handle additional fields
    if issue.descriptionData is not None:
        input_vars["descriptionData"] = issue.descriptionData

    if issue.subscriberIds is not None and len(issue.subscriberIds) > 0:
        input_vars["subscriberIds"] = issue.subscriberIds

    # Convert cycleName to cycleId if provided
    if issue.cycleName is not None:
        from linear_api.get_resources import resource_name_to_id, LinearResourceType
        cycle_id = resource_name_to_id(issue.cycleName, LinearResourceType.CYCLES, team_id)
        input_vars["cycleId"] = cycle_id

    # Convert projectMilestoneName to projectMilestoneId if provided
    if issue.projectMilestoneName is not None and issue.projectName is not None:
        from linear_api.get_resources import resource_name_to_id, LinearResourceType
        milestone_id = resource_name_to_id(issue.projectMilestoneName, LinearResourceType.PROJECT_MILESTONES, team_id)
        input_vars["projectMilestoneId"] = milestone_id

    # Convert templateName to templateId if provided
    if issue.templateName is not None:
        from linear_api.get_resources import resource_name_to_id, LinearResourceType
        template_id = resource_name_to_id(issue.templateName, LinearResourceType.TEMPLATES, team_id)
        input_vars["templateId"] = template_id

    if issue.sortOrder is not None:
        input_vars["sortOrder"] = issue.sortOrder

    if issue.prioritySortOrder is not None:
        input_vars["prioritySortOrder"] = issue.prioritySortOrder

    if issue.subIssueSortOrder is not None:
        input_vars["subIssueSortOrder"] = issue.subIssueSortOrder

    if issue.displayIconUrl is not None:
        input_vars["displayIconUrl"] = issue.displayIconUrl

    if issue.preserveSortOrderOnCreate is not None:
        input_vars["preserveSortOrderOnCreate"] = issue.preserveSortOrderOnCreate

    if issue.createdAt is not None:
        input_vars["createdAt"] = issue.createdAt.isoformat()

    if issue.slaBreachesAt is not None:
        input_vars["slaBreachesAt"] = issue.slaBreachesAt.isoformat()

    if issue.slaStartedAt is not None:
        input_vars["slaStartedAt"] = issue.slaStartedAt.isoformat()

    if issue.slaType is not None:
        input_vars["slaType"] = issue.slaType.value

    if issue.completedAt is not None:
        input_vars["completedAt"] = issue.completedAt.isoformat()

    # Prepare the GraphQL request
    issue_data = {"query": create_issue_mutation, "variables": {"input": input_vars}}

    # Create the issue
    response = call_linear_api(issue_data)
    new_issue_id = response["issueCreate"]["issue"]["id"]

    # If we have a parent ID, set the parent-child relationship
    if parent_id is not None:
        set_parent_response = set_parent_issue(new_issue_id, parent_id)
        # Merge the responses
        response["parentRelationship"] = set_parent_response

    if issue.metadata is not None:
        attachment = LinearAttachmentInput(
            url="http://example.com/metadata",
            title=json.dumps(issue.metadata),
            metadata=issue.metadata,
            issueId=new_issue_id,
        )
        attachment_response = create_attachment(attachment)
        response["attachment"] = attachment_response

    return response


def set_parent_issue(child_id, parent_id) -> Dict:
    link_sub_issue_mutation = """
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        issue {
          id
          title
          parent {
            id
            title
          }
        }
      }
    }
    """

    data = {
        "query": link_sub_issue_mutation,
        "variables": {"id": child_id, "input": {"parentId": parent_id}},
    }

    return call_linear_api(data)


def get_linear_issue(issue_id: str) -> LinearIssue:
    """
    Fetch a Linear issue by ID using GraphQL API
    """
    query = """
    query GetIssueWithAttachments($issueId: String!) {
        issue(id: $issueId) {
            id
            title
            description
            descriptionState
            url
            state { id name type color }
            priority
            priorityLabel
            prioritySortOrder
            sortOrder
            assignee { id name email displayName avatarUrl createdAt updatedAt archivedAt }
            team { id name key description }
            labels{
                nodes {
                        id
                        name
                        color
                      }
                    }
            labelIds
            project { id name description }
            projectMilestone { id name }
            cycle { id name number startsAt endsAt }
            dueDate
            createdAt
            updatedAt
            archivedAt
            startedAt
            completedAt
            startedTriageAt
            triagedAt
            canceledAt
            autoClosedAt
            autoArchivedAt
            addedToProjectAt
            addedToCycleAt
            addedToTeamAt
            slaStartedAt
            slaMediumRiskAt
            slaHighRiskAt
            slaBreachesAt
            slaType
            snoozedUntilAt
            suggestionsGeneratedAt
            number
            parent { id }
            estimate
            branchName
            customerTicketCount
            trashed
            identifier
            subIssueSortOrder
            activitySummary
            reactionData
            integrationSourceType
            creator { id name email displayName avatarUrl createdAt updatedAt archivedAt }
            externalUserCreator { id name email }
            snoozedBy { id name email displayName avatarUrl createdAt updatedAt archivedAt }
            botActor { id name }
            favorite { id createdAt updatedAt }
            sourceComment { id body createdAt updatedAt }
            lastAppliedTemplate { id name }
            recurringIssueTemplate { id name }
            previousIdentifiers
            documentContent { id content }
            attachments {
              nodes {
                id
                url
                title
                subtitle
                metadata
                createdAt
                updatedAt
              }
            }
        }
    }
    """

    out = call_linear_api({"query": query, "variables": {"issueId": issue_id}})["issue"]

    # Process attachments
    attachments = []
    for attachment in out.get("attachments", {}).get("nodes", []):
        attachment["issueId"] = issue_id
        attachments.append(LinearAttachment(**attachment))
    out["attachments"] = attachments

    # Process labels
    labels = []
    for label in out.get("labels", {}).get("nodes", []):
        labels.append(LinearLabel(**label))
    out["labels"] = labels

    # Process nested objects
    if "state" in out and out["state"]:
        out["state"] = LinearState(**out["state"])

    if "team" in out and out["team"]:
        out["team"] = LinearTeam(**out["team"])

    if "assignee" in out and out["assignee"]:
        out["assignee"] = LinearUser(**out["assignee"])

    if "project" in out and out["project"]:
        # The GraphQL query only returns id, name, and description for projects
        # but the LinearProject model requires many more fields
        # Add default values for the required fields that are missing
        project_data = out["project"]
        if project_data:
            # Add required fields with default values if they're missing
            current_time = datetime.now()

            # Import the enum types we need
            from linear_api.domain import ProjectStatusType, FrequencyResolutionType, ProjectStatus

            defaults = {
                "createdAt": current_time,
                "updatedAt": current_time,
                "slugId": "default-slug",
                "url": f"https://linear.app/project/{project_data['id']}",
                "color": "#000000",
                "priority": 0,
                "priorityLabel": "None",
                "prioritySortOrder": 0.0,
                "sortOrder": 0.0,
                "progress": 0.0,
                "status": {"type": ProjectStatusType.PLANNED},  # Create a ProjectStatus object with type field
                "scope": 0.0,
                "frequencyResolution": FrequencyResolutionType.WEEKLY
            }

            # Add default values for any missing required fields
            for key, value in defaults.items():
                if key not in project_data:
                    project_data[key] = value

            # Convert status dict to ProjectStatus object
            if "status" in project_data and isinstance(project_data["status"], dict):
                project_data["status"] = ProjectStatus(**project_data["status"])

            out["project"] = LinearProject(**project_data)

    if "creator" in out and out["creator"]:
        out["creator"] = LinearUser(**out["creator"])

    if "snoozedBy" in out and out["snoozedBy"]:
        out["snoozedBy"] = LinearUser(**out["snoozedBy"])

    if "externalUserCreator" in out and out["externalUserCreator"]:
        out["externalUserCreator"] = ExternalUser(**out["externalUserCreator"])

    if "botActor" in out and out["botActor"]:
        out["botActor"] = ActorBot(**out["botActor"])

    if "favorite" in out and out["favorite"]:
        out["favorite"] = Favorite(**out["favorite"])

    if "sourceComment" in out and out["sourceComment"]:
        out["sourceComment"] = Comment(**out["sourceComment"])

    if "cycle" in out and out["cycle"]:
        out["cycle"] = Cycle(**out["cycle"])

    if "projectMilestone" in out and out["projectMilestone"]:
        out["projectMilestone"] = ProjectMilestone(**out["projectMilestone"])

    if "lastAppliedTemplate" in out and out["lastAppliedTemplate"]:
        out["lastAppliedTemplate"] = Template(**out["lastAppliedTemplate"])

    if "recurringIssueTemplate" in out and out["recurringIssueTemplate"]:
        out["recurringIssueTemplate"] = Template(**out["recurringIssueTemplate"])

    if "documentContent" in out and out["documentContent"]:
        out["documentContent"] = DocumentContent(**out["documentContent"])

    # Process enums
    if "priority" in out:
        out["priority"] = LinearPriority(out["priority"])

    if "integrationSourceType" in out and out["integrationSourceType"]:
        out["integrationSourceType"] = IntegrationService(out["integrationSourceType"])

    # Handle reactionData - API might return a list instead of a dict
    if "reactionData" in out:
        if isinstance(out["reactionData"], list):
            # Convert to empty dict if it's an empty list
            out["reactionData"] = {}

    # Process datetime fields
    datetime_fields = [
        "createdAt", "updatedAt", "archivedAt", "startedAt", "completedAt",
        "startedTriageAt", "triagedAt", "canceledAt", "autoClosedAt", "autoArchivedAt",
        "addedToProjectAt", "addedToCycleAt", "addedToTeamAt", "slaStartedAt",
        "slaMediumRiskAt", "slaHighRiskAt", "slaBreachesAt", "snoozedUntilAt",
        "suggestionsGeneratedAt", "dueDate"
    ]

    for field in datetime_fields:
        if field in out and out[field]:
            out[field] = datetime.fromisoformat(out[field])

    # Handle parent relationship
    if "parent" in out and out["parent"]:
        out["parentId"] = out["parent"]["id"]
    out.pop("parent", None)  # Remove parent field as we've extracted the ID

    # Create the LinearIssue object
    issue = LinearIssue(**out)
    return issue


def get_team_issues(team_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all issues for a specific team with pagination.

    Args:
        team_name: The name of the team to get issues for

    Returns:
        A dictionary mapping issue IDs to issue details

    Raises:
        ValueError: If the team name doesn't exist
    """
    # Convert team name to ID
    team_id = team_name_to_id(team_name)

    # GraphQL query with pagination support
    query = """
    query GetTeamIssues($teamId: ID!, $cursor: String) {
        issues(filter: { team: { id: { eq: $teamId } } }, first: 50, after: $cursor) {
            nodes {
                id
                title
                identifier
                priority
                priorityLabel
                state { id name type color }
                assignee { id name displayName }
                createdAt
                updatedAt
                number
                estimate
                dueDate
                startedAt
                completedAt
                trashed
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Initialize variables for pagination
    cursor = None
    issues = {}

    while True:
        # Call the Linear API with pagination variables
        response = call_linear_api(
            {"query": query, "variables": {"teamId": team_id, "cursor": cursor}}
        )

        # Extract issues and add them to the dictionary
        for issue in response["issues"]["nodes"]:
            issue_id = issue["id"]

            # Process nested objects
            if "state" in issue and issue["state"]:
                issue["state"] = LinearState(**issue["state"])

            if "assignee" in issue and issue["assignee"]:
                issue["assignee"] = LinearUser(**issue["assignee"])

            # Process priority
            if "priority" in issue and issue["priority"] is not None:
                issue["priority"] = LinearPriority(issue["priority"])

            # Process datetime fields
            datetime_fields = ["createdAt", "updatedAt", "dueDate", "startedAt", "completedAt"]
            for field in datetime_fields:
                if field in issue and issue[field]:
                    issue[field] = datetime.fromisoformat(issue[field])

            issues[issue_id] = issue

        # Check if there are more pages
        if not response["issues"]["pageInfo"]["hasNextPage"]:
            break

        # Update cursor for the next page
        cursor = response["issues"]["pageInfo"]["endCursor"]

    return issues


def delete_issue(issue_id: str) -> Dict[str, Any]:
    """
    Delete an issue by its ID.

    Args:
        issue_id: The ID of the issue to delete

    Returns:
        The response from the Linear API

    Raises:
        ValueError: If the issue doesn't exist or can't be deleted
    """
    # GraphQL mutation to delete an issue
    delete_issue_mutation = """
    mutation DeleteIssue($issueId: String!) {
        issueDelete(id: $issueId) {
            success
        }
    }
    """

    # Prepare the GraphQL request
    variables = {"issueId": issue_id}

    # Call the Linear API
    response = call_linear_api({"query": delete_issue_mutation, "variables": variables})

    # Check if the deletion was successful
    if response is None or not response.get("issueDelete", {}).get("success", False):
        raise ValueError(f"Failed to delete issue with ID: {issue_id}")

    return response


def create_attachment(attachment: LinearAttachmentInput):
    mutation = """
    mutation CreateAttachment($input: AttachmentCreateInput!) {
        attachmentCreate(input: $input) {
            success
            attachment {
                id
                url
                title
                subtitle
                metadata
            }
        }
    }
    """

    variables = {
        "input": {
            "issueId": attachment.issueId,
            "url": attachment.url,
            "title": attachment.title,
            "subtitle": attachment.subtitle,
            "metadata": attachment.metadata,
        }
    }

    query = {"query": mutation, "variables": variables}

    return call_linear_api(query)


def update_issue(issue_id: str, update_data: LinearIssueUpdateInput) -> Dict[str, Any]:
    """
    Update an existing issue in Linear.

    Args:
        issue_id: The ID of the issue to update
        update_data: LinearIssueUpdateInput object containing the fields to update

    Returns:
        The response from the Linear API

    Raises:
        ValueError: If teamName, stateName, or projectName doesn't exist
    """
    # GraphQL mutation to update an issue
    update_issue_mutation = """
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue {
          id
          title
          description
          state {
            id
            name
          }
          priority
          assignee {
            id
            name
          }
          project {
            id
            name
          }
        }
      }
    }
    """

    # Convert the Pydantic model to a dictionary, excluding None values
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

    # Build the input variables based on what's provided in update_data
    input_vars = {}

    # Helper function to handle name conversions
    def _handle_name_conversions(update_dict, team_id, input_vars):
        if "stateName" in update_dict:
            state_id = state_name_to_id(update_dict.pop("stateName"), team_id)
            input_vars["stateId"] = state_id

        if "projectName" in update_dict:
            project_id = project_name_to_id(update_dict.pop("projectName"), team_id)
            input_vars["projectId"] = project_id

    # Handle fields that need conversion
    team_id = None
    if "teamName" in update_dict:
        team_id = team_name_to_id(update_dict.pop("teamName"))
        input_vars["teamId"] = team_id
    elif "stateName" in update_dict or "projectName" in update_dict or "cycleName" in update_dict or "projectMilestoneName" in update_dict or "templateName" in update_dict:
        # If teamName is not provided but other name fields are, we need to get the issue first
        issue = get_linear_issue(issue_id)
        team_id = issue.team.id

    # Handle stateName and projectName conversions if we have a team_id
    if team_id is not None:
        _handle_name_conversions(update_dict, team_id, input_vars)

    # Handle priority as an enum value
    if "priority" in update_dict and isinstance(update_dict["priority"], LinearPriority):
        input_vars["priority"] = update_dict.pop("priority").value

    # Handle datetime fields as ISO strings
    datetime_fields = ["dueDate", "createdAt", "slaBreachesAt", "slaStartedAt", "snoozedUntilAt", "completedAt"]
    for field in datetime_fields:
        if field in update_dict and isinstance(update_dict[field], datetime):
            input_vars[field] = update_dict.pop(field).isoformat()

    # Handle SLADayCountType enum
    if "slaType" in update_dict and isinstance(update_dict["slaType"], SLADayCountType):
        input_vars["slaType"] = update_dict.pop("slaType").value

    # Handle additional name-to-id conversions
    if team_id is not None:
        from linear_api.get_resources import resource_name_to_id, LinearResourceType

        # Convert cycleName to cycleId if provided
        if "cycleName" in update_dict:
            cycle_id = resource_name_to_id(update_dict.pop("cycleName"), LinearResourceType.CYCLES, team_id)
            input_vars["cycleId"] = cycle_id

        # Convert projectMilestoneName to projectMilestoneId if provided
        if "projectMilestoneName" in update_dict:
            milestone_id = resource_name_to_id(update_dict.pop("projectMilestoneName"), LinearResourceType.PROJECT_MILESTONES, team_id)
            input_vars["projectMilestoneId"] = milestone_id

        # Convert templateName to templateId if provided
        if "templateName" in update_dict:
            template_id = resource_name_to_id(update_dict.pop("templateName"), LinearResourceType.TEMPLATES, team_id)
            input_vars["templateId"] = template_id

    # Add all remaining fields directly to input_vars
    input_vars.update(update_dict)

    # Prepare the GraphQL request
    data = {"query": update_issue_mutation, "variables": {"id": issue_id, "input": input_vars}}

    # Call the Linear API
    response = call_linear_api(data)

    # Check if the update was successful
    if response is None or not response.get("issueUpdate", {}).get("success", False):
        raise ValueError(f"Failed to update issue with ID: {issue_id}")

    return response


if __name__ == "__main__":
    issue = get_linear_issue("4739f616-353c-4782-9e44-935e7b10d0bc")
    print(issue)
