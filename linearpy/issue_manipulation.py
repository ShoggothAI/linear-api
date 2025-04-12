from typing import Optional, Dict, Any

from datetime import datetime

from linearpy.call_linear_api import call_linear_api
from linearpy.domain import LinearAttachment, LinearIssue, LinearLabel, LinearState, LinearUser, LinearProject, \
    LinearTeam, LinearPriority, LinearIssueInput, LinearAttachmentInput
from linearpy.get_resources import team_name_to_id, state_name_to_id, project_name_to_id


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

    # Prepare the GraphQL request
    issue_data = {
        "query": create_issue_mutation,
        "variables": {
            "input": input_vars
        }
    }

    # Create the issue
    response = call_linear_api(issue_data)

    # If we have a parent ID, set the parent-child relationship
    if parent_id is not None:
        child_id = response["issueCreate"]["issue"]["id"]
        set_parent_response = set_parent_issue(child_id, parent_id)
        # Merge the responses
        response["parentRelationship"] = set_parent_response

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
        "variables": {
            "id": child_id,
            "input": {
                "parentId": parent_id
            }
        }
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
            url
            state { id name type color }
            priority
            assignee { id name email displayName }
            team { id name key description }
            labels{
                nodes {
                        id
                        name
                        color
                      }
                    }
            project { id name description }
            dueDate
            createdAt
            updatedAt
            archivedAt
            number
            parent { id }
            estimate
            branchName
            customerTicketCount
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
    attachments = []
    for attachment in out["attachments"]["nodes"]:
        attachment["issueId"] = issue_id
        attachments.append(LinearAttachment(**attachment))
    labels = []
    for label in out["labels"]["nodes"]:
        labels.append(LinearLabel(**label))

    out["attachments"] = attachments
    out["state"] = LinearState(**out["state"])
    out["team"] = LinearTeam(**out["team"])
    out["labels"] = labels
    if out["assignee"]:
        out["assignee"] = LinearUser(**out["assignee"])
    if out["project"]:
        out["project"] = LinearProject(**out["project"])
    out["priority"] = LinearPriority(out["priority"])
    if out["dueDate"]:
        out["dueDate"] = datetime.fromisoformat(out["dueDate"])
    out["createdAt"] = datetime.fromisoformat(out["createdAt"])
    out["updatedAt"] = datetime.fromisoformat(out["updatedAt"])
    if out["archivedAt"]:
        out["archivedAt"] = datetime.fromisoformat(out["archivedAt"])
    parent = out.pop("parent")
    if parent:
        out["parentId"] = parent("id")

    issue = LinearIssue(**out)
    return issue



def create_attachment(attachment:LinearAttachmentInput):
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
            "metadata": attachment.metadata
        }
    }

    query = {"query": mutation, "variables": variables}

    return call_linear_api(query)

if __name__== "__main__":
    issue = get_linear_issue('4739f616-353c-4782-9e44-935e7b10d0bc')
    print(issue)