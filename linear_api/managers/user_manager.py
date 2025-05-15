"""
User manager for Linear API.

This module provides the UserManager class for working with Linear users.
"""

from typing import Dict, List, Any

from .base_manager import BaseManager
from ..domain import (
    LinearUser, LinearTeam, LinearIssue,
    Draft, IssueDraft
)
from ..utils import enrich_with_client


class UserManager(BaseManager[LinearUser]):
    """
    Manager for working with Linear users.

    This class provides methods for retrieving users and user-related resources.
    """

    @enrich_with_client
    def get(self, user_id: str) -> LinearUser:
        """
        Fetch a Linear user by ID.

        Args:
            user_id: The ID of the user to fetch

        Returns:
            A LinearUser object with the user details

        Raises:
            ValueError: If the user doesn't exist
        """
        # Check cache first
        cached_user = self._cache_get("users_by_id", user_id)
        if cached_user:
            return cached_user

        query = """
       query GetUser($userId: String!) {
           user(id: $userId) {
               # Basic fields
               id
               createdAt
               updatedAt
               archivedAt
               name
               displayName
               email
               avatarUrl

               # Additional scalar fields
               active
               admin
               app
               avatarBackgroundColor
               calendarHash
               createdIssueCount
               description
               disableReason
               guest
               initials
               inviteHash
               isMe
               lastSeen
               statusEmoji
               statusLabel
               statusUntilAt
               timezone
               url

               # Basic information about complex objects
               organization {
                   id
                   name
               }
           }
       }
       """

        response = self._execute_query(query, {"userId": user_id})

        if not response or "user" not in response or not response["user"]:
            raise ValueError(f"User with ID {user_id} not found")

        user = LinearUser(**response["user"])

        # Cache the user
        self._cache_set("users_by_id", user_id, user)

        # Also cache the email mapping
        if user.email:
            self._cache_set("user_id_by_email", user.email, user.id)

        # Also cache name mapping
        if user.name:
            self._cache_set("user_id_by_name", user.name, user.id)
        if user.displayName:
            self._cache_set("user_id_by_name", user.displayName, user.id)

        return user

    @enrich_with_client
    def get_all(self) -> Dict[str, LinearUser]:
        """
        Get all users in the organization.

        Returns:
            A dictionary mapping user IDs to LinearUser objects
        """
        # Check cache first
        cached_users = self._cache_get("all_users", "all")
        if cached_users:
            return cached_users

        # First, get all user IDs and emails
        query = """
       query($cursor: String) {
           users(first: 50, after: $cursor) {
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

        # Get the raw response first to access both nodes and pageInfo
        response = self._execute_query(query, {"cursor": None})

        if not response or "users" not in response or "nodes" not in response["users"]:
            return {}

        # Use the enhanced pagination method to get all user IDs
        user_nodes = self._handle_pagination(
            query,
            {},
            ["users", "nodes"]
        )

        # Convert to dictionary of ID -> LinearUser
        users = {}
        for user_obj in user_nodes:
            try:
                user = self.get(user_obj["id"])
                users[user.id] = user
            except Exception as e:
                # Log error but continue with other users
                print(f"Error fetching user {user_obj['id']}: {e}")

        # Cache all users
        self._cache_set("all_users", "all", users)

        return users

    def get_email_map(self) -> Dict[str, str]:
        """
        Get a mapping of user IDs to their emails.

        Returns:
            A dictionary mapping user IDs to email addresses
        """
        # Check cache first
        cached_map = self._cache_get("email_map", "all")
        if cached_map:
            return cached_map

        query = """
       query($cursor: String) {
           users(first: 50, after: $cursor) {
               nodes {
                   id
                   email
               }
               pageInfo {
                   hasNextPage
                   endCursor
               }
           }
       }
       """

        # Используем улучшенный метод пагинации для получения всех пользователей
        user_nodes = self._handle_pagination(
            query,
            {},
            ["users", "nodes"]
        )

        email_map = {user["id"]: user["email"] for user in user_nodes if "email" in user}

        # Cache the email map
        self._cache_set("email_map", "all", email_map)

        # Also cache individual email to ID mappings
        for user_id, email in email_map.items():
            self._cache_set("user_id_by_email", email, user_id)

        return email_map

    def get_id_by_email(self, email: str) -> str:
        """
        Get a user ID by their email address.

        Args:
            email: The email address of the user

        Returns:
            The user ID

        Raises:
            ValueError: If the user is not found
        """
        # Check cache first
        cached_id = self._cache_get("user_id_by_email", email)
        if cached_id:
            return cached_id

        # Get the email map
        email_map = self.get_email_map()

        # Invert the map (email -> id)
        id_map = {v: k for k, v in email_map.items()}

        if email in id_map:
            # Cache the result
            self._cache_set("user_id_by_email", email, id_map[email])
            return id_map[email]

        raise ValueError(f"User with email '{email}' not found")

    def get_id_by_name(self, name: str) -> str:
        """
        Get a user ID by their name (fuzzy match).

        This will find a user with the closest matching name.

        Args:
            name: The name of the user (displayName or name)

        Returns:
            The user ID

        Raises:
            ValueError: If no matching user is found
        """
        # Check cache first
        cached_id = self._cache_get("user_id_by_name", name)
        if cached_id:
            return cached_id

        # Get all users
        query = """
       query($cursor: String) {
           users(first: 50, after: $cursor) {
               nodes {
                   id
                   name
                   displayName
               }
               pageInfo {
                   hasNextPage
                   endCursor
               }
           }
       }
       """

        # Use pagination to get all users
        user_nodes = self._handle_pagination(
            query,
            {},
            ["users", "nodes"]
        )

        # First, look for exact matches
        for user in user_nodes:
            if user["name"] == name or user["displayName"] == name:
                self._cache_set("user_id_by_name", name, user["id"])
                return user["id"]

        # Then, look for case-insensitive matches
        name_lower = name.lower()
        for user in user_nodes:
            if user["name"].lower() == name_lower or user["displayName"].lower() == name_lower:
                self._cache_set("user_id_by_name", name, user["id"])
                return user["id"]

        # Then, look for partial matches
        for user in user_nodes:
            if (
                    name_lower in user["name"].lower()
                    or name_lower in user["displayName"].lower()
            ):
                self._cache_set("user_id_by_name", name, user["id"])
                return user["id"]

        raise ValueError(f"No user found matching '{name}'")

    @enrich_with_client
    def get_me(self) -> LinearUser:
        """
        Get the current user (based on the API key).

        Returns:
            A LinearUser object representing the current user
        """
        # Check cache first
        cached_user = self._cache_get("current_user", "me")
        if cached_user:
            return cached_user

        query = """
       query {
           viewer {
               id
           }
       }
       """

        response = self._execute_query(query)

        if not response or "viewer" not in response or not response["viewer"]:
            raise ValueError("Could not determine current user")

        # Get the full user details
        user = self.get(response["viewer"]["id"])

        # Cache the current user
        self._cache_set("current_user", "me", user)

        return user

    @enrich_with_client
    def get_assigned_issues(self, user_id: str) -> Dict[str, LinearIssue]:
        """
        Get issues assigned to a user.

        Args:
            user_id: The ID of the user

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        # Check cache first
        cached_issues = self._cache_get("assigned_issues_by_user", user_id)
        if cached_issues:
            return cached_issues

        query = """
        query($userId: ID!, $cursor: String) {
         issues(filter: { assignee: { id: { eq: $userId } } }, first: 50, after: $cursor) {
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

        # Use pagination to get all assigned issue IDs
        issue_nodes = self._handle_pagination(
            query,
            {"userId": user_id},
            ["issues", "nodes"]
        )

        # Convert to dictionary of ID -> LinearIssue
        issues = {}
        for issue_obj in issue_nodes:
            try:
                issue = self.client.issues.get(issue_obj["id"])
                issues[issue.id] = issue
            except Exception as e:
                # Log error but continue with other issues
                print(f"Error fetching assigned issue {issue_obj['id']}: {e}")

        # Cache the result
        self._cache_set("assigned_issues_by_user", user_id, issues)

        return issues

    def get_team_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get team memberships for a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of team membership data (dictionary format since TeamMembership model might be incomplete)
        """
        # Check cache first
        cached_memberships = self._cache_get("team_memberships_by_user", user_id)
        if cached_memberships:
            return cached_memberships

        query = """
       query($userId: String!, $cursor: String) {
         user(id: $userId) {
           teamMemberships(first: 50, after: $cursor) {
             nodes {
               id
               createdAt
               updatedAt
               owner
               team {
                 id
                 name
                 key
                 description
                 color
                 icon
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

        # Get the raw response
        response = self._execute_query(query, {"userId": user_id, "cursor": None})

        if not response or "user" not in response or not response["user"] or "teamMemberships" not in response["user"]:
            return []

        # Use the improved helper method to extract and process the nodes
        membership_nodes = self._handle_pagination(
            query,
            {"userId": user_id},
            ["user", "teamMemberships", "nodes"]
        )

        # Process team data within memberships
        for membership in membership_nodes:
            if "team" in membership and membership["team"]:
                team_data = membership["team"]
                membership["team"] = LinearTeam(**team_data)

        # Cache the result
        self._cache_set("team_memberships_by_user", user_id, membership_nodes)

        return membership_nodes

    @enrich_with_client
    def get_teams(self, user_id: str) -> List[LinearTeam]:
        """
        Get teams that a user is a member of.

        Args:
            user_id: The ID of the user

        Returns:
            A list of LinearTeam objects
        """
        # First, get team memberships
        memberships = self.get_team_memberships(user_id)

        # Extract team objects from memberships
        teams = []
        for membership in memberships:
            if "team" in membership and isinstance(membership["team"], LinearTeam):
                teams.append(membership["team"])

        return teams

    def get_created_issues(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get issues created by a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of issue data dictionaries
        """
        # Check cache first
        cached_issues = self._cache_get("created_issues_by_user", user_id)
        if cached_issues:
            return cached_issues

        query = """
        query($userId: String!, $cursor: String) {
         user(id: $userId) {
           createdIssues(first: 50, after: $cursor) {
             nodes {
               id
               title
               description
               state {
                 id
                 name
                 type
               }
               priority
               priorityLabel
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

        # Get the initial response
        response = self._execute_query(query, {"userId": user_id, "cursor": None})

        if not response or "user" not in response or not response["user"] or "createdIssues" not in response["user"]:
            return []

        # Use our improved extraction method with pagination
        issues = self._handle_pagination(
            query,
            {"userId": user_id},
            ["user", "createdIssues", "nodes"]
        )

        # Cache the result
        self._cache_set("created_issues_by_user", user_id, issues)

        return issues

    def get_drafts(self, user_id: str) -> List[Draft]:
        """
        Get document drafts created by a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of Draft objects for the user
        """
        # Check cache first
        cached_drafts = self._cache_get("drafts_by_user", user_id)
        if cached_drafts:
            return cached_drafts

        query = """
        query($userId: String!, $cursor: String) {
         user(id: $userId) {
           drafts(first: 50, after: $cursor) {
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

        # Use the extract_and_cache method to simplify implementation
        response = self._execute_query(query, {"userId": user_id, "cursor": None})

        if not response or "user" not in response or not response["user"]:
            return []

        # Use pagination and automatic model conversion
        drafts = self._handle_pagination(
            query,
            {"userId": user_id},
            ["user", "drafts", "nodes"],
            Draft  # Pass the model class for automatic conversion
        )

        # Cache the result
        self._cache_set("drafts_by_user", user_id, drafts)

        return drafts

    def get_issue_drafts(self, user_id: str) -> List[IssueDraft]:
        """
        Get issue drafts created by a user.

        Args:
            user_id: The ID of the user

        Returns:
            A list of IssueDraft objects for the user
        """
        # Check cache first
        cached_drafts = self._cache_get("issue_drafts_by_user", user_id)
        if cached_drafts:
            return cached_drafts

        query = """
       query($userId: String!, $cursor: String) {
         user(id: $userId) {
           issueDrafts(first: 50, after: $cursor) {
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

        # Get the raw response
        response = self._execute_query(query, {"userId": user_id, "cursor": None})

        if not response or "user" not in response or not response["user"] or "issueDrafts" not in response["user"]:
            return []

        # Use pagination to get all draft nodes
        draft_nodes = self._handle_pagination(
            query,
            {"userId": user_id},
            ["user", "issueDrafts", "nodes"]
        )

        # Process each draft node
        drafts = []
        for draft in draft_nodes:
            # Convert team if present
            if "team" in draft and draft["team"]:
                draft["team"] = LinearTeam(**draft["team"])

            # Create IssueDraft object
            drafts.append(IssueDraft(**draft))

        # Cache the result
        self._cache_set("issue_drafts_by_user", user_id, drafts)

        return drafts

    def invalidate_cache(self) -> None:
        """
        Invalidate all user-related caches.
        This should be called after any mutating operations.
        """
        self._cache_clear()
