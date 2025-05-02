"""
Issue manager for Linear API.

This module provides the IssueManager class for working with Linear issues.
"""

import json
from datetime import datetime
from typing import Dict, List, Any

from .base_manager import BaseManager
from ..domain import (
    LinearIssue,
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearAttachmentInput,
    LinearPriority,
)


class IssueManager(BaseManager[LinearIssue]):
    """
    Manager for working with Linear issues.

    This class provides methods for creating, retrieving, updating, and deleting
    issues in Linear, as well as working with issue-related resources like
    attachments, comments, and history.
    """

    def get(self, issue_id: str) -> LinearIssue:
        """
        Fetch a Linear issue by ID.

        Args:
            issue_id: The ID of the issue to fetch

        Returns:
            A LinearIssue object with the issue details

        Raises:
            ValueError: If the issue doesn't exist
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

        response = self._execute_query(query, {"issueId": issue_id})

        if not response or "issue" not in response or not response["issue"]:
            raise ValueError(f"Issue with ID {issue_id} not found")

        # Process the response using the existing _process_issue_data function
        from ..utils.issue_processor import process_issue_data
        issue = process_issue_data(response["issue"])

        return issue

    def create(self, issue: LinearIssueInput) -> LinearIssue:
        """
        Create a new issue in Linear.

        Args:
            issue: The issue data to create

        Returns:
            The created LinearIssue

        Raises:
            ValueError: If the issue creation fails
        """
        # Convert teamName to teamId
        team_id = self.client.teams.get_id_by_name(issue.teamName)

        # GraphQL mutation to create an issue
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            issue {
              id
            }
          }
        }
        """

        # Build input variables from the issue object
        input_vars = self._build_issue_input_vars(issue, team_id)

        # Create the issue
        response = self._execute_query(mutation, {"input": input_vars})

        if not response or "issueCreate" not in response or not response["issueCreate"]["issue"]:
            raise ValueError(f"Failed to create issue '{issue.title}'")

        new_issue_id = response["issueCreate"]["issue"]["id"]

        # If we have a parent ID, set the parent-child relationship
        if issue.parentId is not None:
            self._set_parent_issue(new_issue_id, issue.parentId)

        # If we have metadata, create an attachment for it
        if issue.metadata is not None:
            attachment = LinearAttachmentInput(
                url=f"urn:linear:metadata:{new_issue_id}",
                title=json.dumps(issue.metadata),
                metadata=issue.metadata,
                issueId=new_issue_id,
            )
            self.create_attachment(attachment)

        # Return the full issue object
        return self.get(new_issue_id)

    def update(self, issue_id: str, update_data: LinearIssueUpdateInput) -> LinearIssue:
        """
        Update an existing issue in Linear.

        Args:
            issue_id: The ID of the issue to update
            update_data: The issue data to update

        Returns:
            The updated LinearIssue

        Raises:
            ValueError: If the issue update fails
        """
        # GraphQL mutation to update an issue
        mutation = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
            }
          }
        }
        """

        # Build input variables from the update data
        input_vars = self._build_issue_update_vars(issue_id, update_data)

        # Update the issue
        response = self._execute_query(mutation, {"id": issue_id, "input": input_vars})

        if not response or "issueUpdate" not in response or not response["issueUpdate"]["success"]:
            raise ValueError(f"Failed to update issue with ID: {issue_id}")

        # If we have metadata, create or update an attachment for it
        if update_data.metadata is not None:
            attachment = LinearAttachmentInput(
                url=f"urn:linear:metadata:{issue_id}",
                title=json.dumps(update_data.metadata),
                metadata=update_data.metadata,
                issueId=issue_id,
            )
            self.create_attachment(attachment)

        # Return the updated issue
        return self.get(issue_id)

    def delete(self, issue_id: str) -> bool:
        """
        Delete an issue by its ID.

        Args:
            issue_id: The ID of the issue to delete

        Returns:
            True if the deletion was successful

        Raises:
            ValueError: If the issue doesn't exist or can't be deleted
        """
        mutation = """
        mutation DeleteIssue($issueId: String!) {
            issueDelete(id: $issueId) {
                success
            }
        }
        """

        response = self._execute_query(mutation, {"issueId": issue_id})

        if not response or not response.get("issueDelete", {}).get("success", False):
            raise ValueError(f"Failed to delete issue with ID: {issue_id}")

        return True

    def get_by_team(self, team_name: str) -> Dict[str, LinearIssue]:
        """
        Get all issues for a specific team.

        Args:
            team_name: The name of the team to get issues for

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects

        Raises:
            ValueError: If the team name doesn't exist
        """
        # Convert team name to ID
        team_id = self.client.teams.get_id_by_name(team_name)

        # GraphQL query with pagination support
        query = """
        query GetTeamIssues($teamId: ID!, $cursor: String) {
            issues(filter: { team: { id: { eq: $teamId } } }, first: 50, after: $cursor) {
                nodes {
                    id
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """

        # Get all issue IDs for this team
        issue_objects = self._handle_pagination(
            query,
            {"teamId": team_id},
            ["issues", "nodes"]
        )

        # Convert to dictionary of ID -> LinearIssue
        issues = {}
        for issue_obj in issue_objects:
            try:
                issue = self.get(issue_obj["id"])
                issues[issue.id] = issue
            except Exception as e:
                # Log error but continue with other issues
                print(f"Error fetching issue {issue_obj['id']}: {e}")

        return issues

    def get_by_project(self, project_id: str) -> Dict[str, LinearIssue]:
        """
        Get all issues for a specific project.

        Args:
            project_id: The ID of the project to get issues for

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        query = """
        query($projectId: String!, $cursor: String) {
          project(id: $projectId) {
            issues(first: 100, after: $cursor) {
              nodes {
                id
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """

        # Get all issue IDs for this project
        issue_objects = self._handle_pagination(
            query,
            {"projectId": project_id},
            ["project", "issues", "nodes"]
        )

        # Convert to dictionary of ID -> LinearIssue
        issues = {}
        for issue_obj in issue_objects:
            try:
                issue = self.get(issue_obj["id"])
                issues[issue.id] = issue
            except Exception as e:
                # Log error but continue with other issues
                print(f"Error fetching issue {issue_obj['id']}: {e}")

        return issues

    def get_all(self) -> Dict[str, LinearIssue]:
        """
        Get all issues from all teams in the organization.

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        query = """
        query($cursor: String) {
          issues(first: 100, after: $cursor) {
            nodes {
              id
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """

        # Get all issue IDs
        issue_objects = self._handle_pagination(
            query,
            {},
            ["issues", "nodes"]
        )

        # Convert to dictionary of ID -> LinearIssue
        issues = {}
        batch_size = 20
        all_issue_ids = [issue["id"] for issue in issue_objects]

        for i in range(0, len(all_issue_ids), batch_size):
            batch = all_issue_ids[i:i + batch_size]
            print(
                f"Processing batch {i // batch_size + 1}/{(len(all_issue_ids) - 1) // batch_size + 1} ({len(batch)} issues)")

            for issue_id in batch:
                try:
                    issue = self.get(issue_id)
                    issues[issue_id] = issue
                except Exception as e:
                    # Log error but continue with other issues
                    print(f"Error fetching issue {issue_id}: {e}")

        return issues

    def create_attachment(self, attachment: LinearAttachmentInput) -> Dict[str, Any]:
        """
        Create an attachment for an issue.

        Args:
            attachment: The attachment data to create

        Returns:
            The created attachment data
        """
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

        return self._execute_query(mutation, variables)

    def get_attachments(self, issue_id: str) -> List[Dict[str, Any]]:
        """
        Get attachments for an issue.

        Args:
            issue_id: The ID of the issue to get attachments for

        Returns:
            A list of attachment data
        """
        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            attachments {
              nodes {
                id
                title
                url
                subtitle
                metadata
                createdAt
                updatedAt
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"issueId": issue_id})

        if response and "issue" in response and response["issue"] and "attachments" in response["issue"]:
            return response["issue"]["attachments"]["nodes"]

        return []

    def get_comments(self, issue_id: str) -> List[Dict[str, Any]]:
        """
        Get comments for an issue.

        Args:
            issue_id: The ID of the issue to get comments for

        Returns:
            A list of comment data
        """
        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            comments {
              nodes {
                id
                body
                user {
                  id
                  name
                }
                createdAt
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"issueId": issue_id})

        if response and "issue" in response and response["issue"] and "comments" in response["issue"]:
            return response["issue"]["comments"]["nodes"]

        return []

    def get_history(self, issue_id: str) -> List[Dict[str, Any]]:
        """
        Get the change history for an issue.

        Args:
            issue_id: The ID of the issue to get history for

        Returns:
            A list of history items
        """
        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            history(first: 50) {
              nodes {
                id
                createdAt
                fromState {
                  id
                  name
                }
                toState {
                  id
                  name
                }
                actor {
                  ... on User {
                    id
                    name
                  }
                }
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"issueId": issue_id})

        if response and "issue" in response and response["issue"] and "history" in response["issue"]:
            return response["issue"]["history"]["nodes"]

        return []

    def _set_parent_issue(self, child_id: str, parent_id: str) -> Dict[str, Any]:
        """
        Set a parent-child relationship between issues.

        Args:
            child_id: The ID of the child issue
            parent_id: The ID of the parent issue

        Returns:
            The API response
        """
        mutation = """
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

        return self._execute_query(
            mutation,
            {"id": child_id, "input": {"parentId": parent_id}}
        )

    def _build_issue_input_vars(self, issue: LinearIssueInput, team_id: str) -> Dict[str, Any]:
        """
        Build input variables for creating an issue.

        Args:
            issue: The issue data
            team_id: The ID of the team

        Returns:
            Input variables for the GraphQL mutation
        """
        # Start with required fields
        input_vars = {
            "title": issue.title,
            "teamId": team_id,
        }

        # Add optional fields if they are set
        if issue.description is not None:
            input_vars["description"] = issue.description

        # Handle priority as an enum value
        if issue.priority is not None:
            input_vars["priority"] = issue.priority.value

        # Convert stateName to stateId if provided
        if issue.stateName is not None:
            state_id = self.client.teams.get_state_id_by_name(issue.stateName, team_id)
            input_vars["stateId"] = state_id

        if issue.assigneeId is not None:
            input_vars["assigneeId"] = issue.assigneeId

        # Convert projectName to projectId if provided
        if issue.projectName is not None:
            project_id = self.client.projects.get_id_by_name(issue.projectName, team_id)
            input_vars["projectId"] = project_id

        if issue.labelIds is not None and len(issue.labelIds) > 0:
            input_vars["labelIds"] = issue.labelIds

        if issue.dueDate is not None:
            # Format datetime as ISO string
            input_vars["dueDate"] = issue.dueDate.isoformat()

        if issue.estimate is not None:
            input_vars["estimate"] = issue.estimate

        # Handle additional fields
        optional_fields = [
            "descriptionData", "subscriberIds", "sortOrder", "prioritySortOrder",
            "subIssueSortOrder", "displayIconUrl", "preserveSortOrderOnCreate"
        ]

        for field in optional_fields:
            value = getattr(issue, field, None)
            if value is not None:
                input_vars[field] = value

        # Handle datetime fields
        datetime_fields = ["createdAt", "slaBreachesAt", "slaStartedAt", "completedAt"]
        for field in datetime_fields:
            value = getattr(issue, field, None)
            if value is not None:
                input_vars[field] = value.isoformat()

        # Handle enum fields
        if issue.slaType is not None:
            input_vars["slaType"] = issue.slaType.value

        return input_vars

    def _build_issue_update_vars(self, issue_id: str, update_data: LinearIssueUpdateInput) -> Dict[str, Any]:
        """
        Build input variables for updating an issue.

        Args:
            issue_id: The ID of the issue to update
            update_data: The update data

        Returns:
            Input variables for the GraphQL mutation
        """
        # Convert the Pydantic model to a dictionary, excluding None values
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}

        # Build the input variables
        input_vars = {}

        # Handle teamName conversion
        team_id = None
        if "teamName" in update_dict:
            team_id = self.client.teams.get_id_by_name(update_dict.pop("teamName"))
            input_vars["teamId"] = team_id
        elif "stateName" in update_dict or "projectName" in update_dict:
            # If teamName is not provided but other name fields are, we need to get the issue first
            issue = self.get(issue_id)
            team_id = issue.team.id

        # Handle stateName conversion
        if "stateName" in update_dict and team_id:
            state_id = self.client.teams.get_state_id_by_name(update_dict.pop("stateName"), team_id)
            input_vars["stateId"] = state_id

        # Handle projectName conversion
        if "projectName" in update_dict and team_id:
            project_id = self.client.projects.get_id_by_name(update_dict.pop("projectName"), team_id)
            input_vars["projectId"] = project_id

        # Handle priority as an enum value
        if "priority" in update_dict and isinstance(update_dict["priority"], LinearPriority):
            input_vars["priority"] = update_dict.pop("priority").value

        # Handle datetime fields
        datetime_fields = ["dueDate", "createdAt", "slaBreachesAt", "slaStartedAt", "snoozedUntilAt", "completedAt"]
        for field in datetime_fields:
            if field in update_dict and isinstance(update_dict[field], datetime):
                input_vars[field] = update_dict.pop(field).isoformat()

        # Handle enum fields
        if "slaType" in update_dict:
            input_vars["slaType"] = update_dict.pop("slaType").value

        # Add all remaining fields directly to input_vars
        input_vars.update(update_dict)

        return input_vars
