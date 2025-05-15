"""
Issue manager for Linear API.

This module provides the IssueManager class for working with Linear issues.
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from urllib.parse import urlparse

from .base_manager import BaseManager
from ..domain import IssueRelation, CustomerNeedResponse
from ..domain import (
    LinearIssue,
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearAttachmentInput,
    LinearPriority,
    Comment,
    LinearUser, Reaction
)
from ..utils import process_issue_data, enrich_with_client


class IssueManager(BaseManager[LinearIssue]):
    """
    Manager for working with Linear issues.

    This class provides methods for creating, retrieving, updating, and deleting
    issues in Linear, as well as working with issue-related resources like
    attachments, comments, and history.
    """

    @enrich_with_client
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
        # Check cache first
        cached_issue = self._cache_get("issues_by_id", issue_id)
        if cached_issue:
            return cached_issue

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
        issue = process_issue_data(response["issue"])

        # Cache the issue
        self._cache_set("issues_by_id", issue_id, issue)

        return issue

    @enrich_with_client
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

        # Invalidate relevant caches after creation
        self._cache_clear("issues_by_team")
        if issue.projectName:
            project_id = self.client.projects.get_id_by_name(issue.projectName, team_id)
            self._cache_invalidate("issues_by_project", project_id)
        self._cache_clear("all_issues")

        # If we have a parent ID, set the parent-child relationship
        if issue.parentId is not None:
            self._set_parent_issue(new_issue_id, issue.parentId)
            # Invalidate parent issue cache
            self._cache_invalidate("issues_by_id", issue.parentId)

        # If we have metadata, create an attachment for it
        if issue.metadata is not None:
            attachment = LinearAttachmentInput(
                url=issue.metadata.get("url", ""),  # TODO ?
                title=json.dumps(issue.metadata),
                metadata=issue.metadata,
                issueId=new_issue_id,
            )
            self.create_attachment(attachment)

        # Return the full issue object
        return self.get(new_issue_id)

    @enrich_with_client
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

        try:
            current_issue = self.get(issue_id)
            parent_id = current_issue.parentId if hasattr(current_issue, 'parentId') else None
            old_state_id = current_issue.state.id if current_issue.state else None
        except ValueError:
            parent_id = None
            old_state_id = None

        # Build input variables from the update data
        input_vars = self._build_issue_update_vars(issue_id, update_data)

        # Update the issue
        response = self._execute_query(mutation, {"id": issue_id, "input": input_vars})

        if not response or "issueUpdate" not in response or not response["issueUpdate"]["success"]:
            raise ValueError(f"Failed to update issue with ID: {issue_id}")

        self._cache_invalidate("issues_by_id", issue_id)

        if parent_id:
            self._cache_invalidate("children_by_issue", parent_id)

        self._cache_invalidate("children_by_issue", issue_id)

        # If team or project was changed, invalidate those caches too
        if hasattr(update_data, "teamName") and update_data.teamName:
            self._cache_clear("issues_by_team")
        if hasattr(update_data, "projectName") and update_data.projectName:
            # We can't know which project it was moved from/to, so clear all project caches
            self._cache_clear("issues_by_project")

        # If parent was changed, invalidate parent cache
        if hasattr(update_data, "parentId") and update_data.parentId:
            self._cache_invalidate("issues_by_id", update_data.parentId)
            self._cache_invalidate("children_by_issue", update_data.parentId)

        # If we have metadata, create or update an attachment for it
        if update_data.metadata is not None:
            attachment = LinearAttachmentInput(
                url=update_data.metadata.get("url", ""),  # TODO ?
                title=json.dumps(update_data.metadata),
                metadata=update_data.metadata,
                issueId=issue_id,
            )
            self.create_attachment(attachment)

        updated_issue = self.get(issue_id)

        if old_state_id and updated_issue.state and old_state_id != updated_issue.state.id:
            if updated_issue.team and updated_issue.team.id:
                self._cache_clear("states_by_team_id")
                self._cache_clear("states_by_team_id_True")

        return updated_issue

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
        # Get the issue to find its team and project before deletion
        try:
            issue = self.get(issue_id)
            team_id = issue.team.id if issue.team else None
            project_id = issue.project.id if issue.project else None
        except:
            team_id = None
            project_id = None

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

        # Invalidate caches after deletion
        self._cache_invalidate("issues_by_id", issue_id)
        if team_id:
            self._cache_invalidate("issues_by_team", team_id)
        if project_id:
            self._cache_invalidate("issues_by_project", project_id)
        self._cache_clear("all_issues")

        return True

    @enrich_with_client
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

        # Check cache first
        cached_issues = self._cache_get("issues_by_team", team_id)
        if cached_issues:
            return cached_issues

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

        # Get all issue IDs for this team using our improved pagination method
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

        # Cache the result
        self._cache_set("issues_by_team", team_id, issues)

        return issues

    @enrich_with_client
    def get_by_project(self, project_id: str) -> Dict[str, LinearIssue]:
        """
        Get all issues for a specific project.

        Args:
            project_id: The ID of the project to get issues for

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        # Check cache first
        cached_issues = self._cache_get("issues_by_project", project_id)
        if cached_issues:
            return cached_issues

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

        # Get all issue IDs for this project using our improved pagination method
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

        # Cache the result
        self._cache_set("issues_by_project", project_id, issues)

        return issues

    @enrich_with_client
    def get_all(self) -> Dict[str, LinearIssue]:
        """
        Get all issues from all teams in the organization.

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        # Check cache first
        cached_issues = self._cache_get("all_issues", "all")
        if cached_issues:
            return cached_issues

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

        # Get all issue IDs using our improved pagination method
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

        # Cache the result
        self._cache_set("all_issues", "all", issues)

        return issues

    def create_attachment(self, attachment: LinearAttachmentInput) -> Dict[str, Any]:
        """
        Create an attachment for an issue.

        Args:
            attachment: The attachment data to create

        Returns:
            The created attachment data
        """

        def is_valid_url(url):
            if not url:
                return False
            try:
                result = urlparse(url)
                return all([result.scheme in ['http', 'https'], result.netloc])
            except:
                return False

        if not is_valid_url(attachment.url):
            attachment.url = f"https://linear.app/issue/{attachment.issueId}"

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

        response = self._execute_query(mutation, variables)

        # Invalidate issue cache after adding attachment
        self._cache_invalidate("issues_by_id", attachment.issueId)

        return response

    def get_attachments(self, issue_id: str) -> List[Dict[str, Any]]:
        """
        Get attachments for an issue.

        Args:
            issue_id: The ID of the issue to get attachments for

        Returns:
            A list of attachment data
        """
        # Check cache first
        cached_attachments = self._cache_get("attachments_by_issue", issue_id)
        if cached_attachments:
            return cached_attachments

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
               archivedAt
               bodyData
               groupBySource
               source
               sourceType
               creator {
                   id
                   name
                   displayName
               }
               externalUserCreator {
                   id
                   name
                   email
               }
             }
           }
         }
        }
        """

        # Use our extract_and_cache helper method for simpler implementation
        response = self._execute_query(query, {"issueId": issue_id})

        if not response or "issue" not in response:
            return []

        attachments = self._extract_and_cache(
            response,
            ["issue", "attachments"],
            "attachments_by_issue",
            issue_id
        )

        return attachments

    def get_history(self, issue_id: str) -> List[Dict[str, Any]]:
        """
        Get the change history for an issue.

        Args:
            issue_id: The ID of the issue to get history for

        Returns:
            A list of history items
        """
        # Check cache first
        cached_history = self._cache_get("history_by_issue", issue_id)
        if cached_history:
            return cached_history

        query = """
        query($issueId: String!, $cursor: String) {
         issue(id: $issueId) {
           history(first: 50, after: $cursor) {
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
             pageInfo {
               hasNextPage
               endCursor
             }
           }
         }
        }
        """

        # Use our extract_and_cache helper method
        response = self._execute_query(query, {"issueId": issue_id, "cursor": None})

        if not response or "issue" not in response:
            return []

        history = self._extract_and_cache(
            response,
            ["issue", "history"],
            "history_by_issue",
            issue_id
        )

        return history

    def get_comments(self, issue_id: str) -> List[Comment]:
        """
        Get comments for an issue.

        Args:
            issue_id: The ID of the issue to get comments for

        Returns:
            A list of Comment objects
        """
        # Check cache first
        cached_comments = self._cache_get("comments_by_issue", issue_id)
        if cached_comments:
            return cached_comments

        query = """
        query($issueId: String!, $cursor: String) {
         issue(id: $issueId) {
           comments(first: 50, after: $cursor) {
             nodes {
               id
               body
               user {
                 id
                 name
                 displayName
                 email
               }
               createdAt
               updatedAt
             }
             pageInfo {
               hasNextPage
               endCursor
             }
           }
         }
        }
        """

        # Use our improved pagination method with automatic model conversion
        response = self._execute_query(query, {"issueId": issue_id, "cursor": None})

        if not response or "issue" not in response:
            return []

        comments = self._handle_pagination(
            query,
            {"issueId": issue_id},
            ["issue", "comments", "nodes"],
            Comment  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("comments_by_issue", issue_id, comments)

        return comments

    def get_children(self, issue_id: str) -> Dict[str, LinearIssue]:
        """
        Get child issues for an issue.

        Args:
            issue_id: The ID of the parent issue

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        # Check cache first
        cached_children = self._cache_get("children_by_issue", issue_id)
        if cached_children:
            return cached_children

        query = """
        query($parentId: ID!, $cursor: String) {
         issues(filter: { parent: { id: { eq: $parentId } } }, first: 50, after: $cursor) {
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

        # Use our improved pagination method
        issue_nodes = self._handle_pagination(
            query,
            {"parentId": issue_id},
            ["issues", "nodes"]
        )

        # Convert to dictionary of ID -> LinearIssue
        children = {}
        for issue_obj in issue_nodes:
            try:
                issue = self.get(issue_obj["id"])
                children[issue.id] = issue
            except Exception as e:
                # Log error but continue with other issues
                print(f"Error fetching child issue {issue_obj['id']}: {e}")

        # Cache the result
        self._cache_set("children_by_issue", issue_id, children)

        return children

    def get_reactions(self, issue_id: str) -> List[Reaction]:
        """
        Get reactions to an issue.

        Args:
            issue_id: The ID of the issue

        Returns:
            A list of reaction objects
        """
        # Check cache first
        cached_reactions = self._cache_get("reactions_by_issue", issue_id)
        if cached_reactions:
            return cached_reactions

        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            reactions {
              id
              emoji
              user {
                id
                name
                displayName
              }
              createdAt
            }
          }
        }
        """

        response = self._execute_query(query, {"issueId": issue_id})
        if not response or "issue" not in response or not response["issue"] or "reactions" not in response["issue"]:
            return []


        reactions = []
        for reaction_data in response["issue"]["reactions"]:
            try:
                reactions.append(Reaction(**reaction_data))
            except Exception as e:
                print(f"Error converting reaction: {e}")

        self._cache_set("reactions_by_issue", issue_id, reactions)

        return reactions

    @enrich_with_client
    def get_subscribers(self, issue_id: str) -> List[LinearUser]:
        """
        Get subscribers of an issue.

        Args:
            issue_id: The ID of the issue

        Returns:
            A list of LinearUser objects
        """
        # Check cache first
        cached_subscribers = self._cache_get("subscribers_by_issue", issue_id)
        if cached_subscribers:
            return cached_subscribers

        query = """
        query($issueId: String!, $cursor: String) {
         issue(id: $issueId) {
           subscribers(first: 50, after: $cursor) {
             nodes {
               id
               name
               displayName
               email
               avatarUrl
               createdAt
               updatedAt
             }
             pageInfo {
               hasNextPage
               endCursor
             }
           }
         }
        }
        """

        # Use our improved pagination method with automatic model conversion
        response = self._execute_query(query, {"issueId": issue_id, "cursor": None})

        if not response or "issue" not in response:
            return []

        subscribers = self._handle_pagination(
            query,
            {"issueId": issue_id},
            ["issue", "subscribers", "nodes"],
            LinearUser  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("subscribers_by_issue", issue_id, subscribers)

        return subscribers

    def get_relations(self, issue_id: str) -> List[IssueRelation]:
        """
        Get relations for an issue.

        Args:
            issue_id: The ID of the issue

        Returns:
            A list of issue relation objects
        """
        # Check cache first
        cached_relations = self._cache_get("relations_by_issue", issue_id)
        if cached_relations:
            return cached_relations

        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            relations {
              nodes {
                id
                type
                relatedIssue {
                  id
                  title
                }
                issue {
                  id
                  title
                }
                createdAt
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"issueId": issue_id})
        if not response or "issue" not in response or not response["issue"] or "relations" not in response[
            "issue"] or "nodes" not in response["issue"]["relations"]:
            return []

        relations = []
        for relation_data in response["issue"]["relations"]["nodes"]:
            try:
                relations.append(IssueRelation(**relation_data))
            except Exception as e:
                print(f"Error converting relation: {e}")

        # Cache the result
        self._cache_set("relations_by_issue", issue_id, relations)

        return relations

    def get_inverse_relations(self, issue_id: str) -> List[IssueRelation]:
        """
        Get inverse relations for an issue.

        Args:
            issue_id: The ID of the issue

        Returns:
            A list of issue relation objects
        """
        # Check cache first
        cached_relations = self._cache_get("inverse_relations_by_issue", issue_id)
        if cached_relations:
            return cached_relations

        # Запрос для inverseRelations, который является Connection
        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            inverseRelations {
              nodes {
                id
                type
                relatedIssue {
                  id
                  title
                }
                issue {
                  id
                  title
                }
                createdAt
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"issueId": issue_id})

        if not response or "issue" not in response or not response["issue"] or "inverseRelations" not in response[
            "issue"] or "nodes" not in response["issue"]["inverseRelations"]:
            return []

        relations = []
        for relation_data in response["issue"]["inverseRelations"]["nodes"]:
            try:
                relations.append(IssueRelation(**relation_data))
            except Exception as e:
                print(f"Error converting relation: {e}")

        # Cache the result
        self._cache_set("inverse_relations_by_issue", issue_id, relations)

        return relations

    def get_needs(self, issue_id: str) -> List[CustomerNeedResponse]:
        """
        Get customer needs associated with an issue.

        Args:
            issue_id: The ID of the issue

        Returns:
            A list of CustomerNeed objects
        """
        # Check cache first
        cached_needs = self._cache_get("needs_by_issue", issue_id)
        if cached_needs:
            return cached_needs

        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            needs {
              nodes {
                id
                createdAt
                updatedAt
                archivedAt
                priority
                body
                bodyData
                url
                creator {
                  id
                  name
                  displayName
                }
              }
            }
          }
        }
        """

        response = self._execute_query(query, {"issueId": issue_id})

        if not response or "issue" not in response or not response["issue"] or "needs" not in response[
            "issue"] or "nodes" not in response["issue"]["needs"]:
            return []

        needs = []
        for need_data in response["issue"]["needs"]["nodes"]:
            try:
                if "creator" in need_data and need_data["creator"]:
                    need_data["creator"] = LinearUser(**need_data["creator"])

                needs.append(CustomerNeedResponse(**need_data))
            except Exception as e:
                print(f"Error converting need: {e}")

        # Cache the result
        self._cache_set("needs_by_issue", issue_id, needs)

        return needs

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

        response = self._execute_query(
            mutation,
            {"id": child_id, "input": {"parentId": parent_id}}
        )

        # Invalidate caches for both parent and child issues
        self._cache_invalidate("issues_by_id", child_id)
        self._cache_invalidate("issues_by_id", parent_id)

        return response

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

    def invalidate_cache(self) -> None:
        """
        Invalidate all issue-related caches.
        This should be called after any mutating operations.
        """
        self._cache_clear()
