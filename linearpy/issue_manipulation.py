from typing import Optional, Dict, Any

from datetime import datetime

from linearpy.call_linear_api import call_linear_api
from linearpy.domain import LinearAttachment, LinearIssue, LinearLabel, LinearState, LinearUser, LinearProject, \
    LinearTeam, LinearPriority, LinearIssueCreateInput
from linearpy.get_teams import team_name_to_id


def create_issue(issue: LinearIssueCreateInput):

    #TODO: if issue.parentID is not None, set it to none for issue creation,
    # get the child_id from call_linear_api, then call set_parent_issue


    #TODO: modify create_issue_mutation to only include the fields that are set,
    # and to correctly handle LinearPriority

    team_id = team_name_to_id(issue.team.name)

    # GraphQL mutation to create a parent issue
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

    # Data for the parent issue
    issue_data = {
        "query": create_issue_mutation,
        "variables": {
            "input": {
                "teamId": team_id,  # Replace with your team ID
                "title": issue.title,
                "description": issue.description,
                "priority": issue.priority
            }
        }
    }


    return call_linear_api(issue_data)


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



def create_attachment(attachment:LinearAttachment):
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