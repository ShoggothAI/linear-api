from typing import Optional, Dict

from linearpy.call_linear_api import call_linear_api
from linearpy.domain import Issue
from linearpy.get_teams import team_name_to_id


def create_issue(issue: Issue):

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


def set_parent_issue(child_issue: Issue, parent_issue: Issue) -> Dict:
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
            "id": child_issue.id,
            "input": {
                "parentId": parent_issue.id
            }
        }
    }

    return call_linear_api(data)