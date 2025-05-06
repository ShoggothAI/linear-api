"""
User manager for Linear API.

This module provides the UserManager class for working with Linear users.
"""

from typing import Dict

from .base_manager import BaseManager
from ..domain import LinearUser


class UserManager(BaseManager[LinearUser]):
    """
    Manager for working with Linear users.

    This class provides methods for retrieving users and user-related resources.
    """

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
        query {
            users {
                nodes {
                    id
                }
            }
        }
        """

        response = self._execute_query(query)

        if not response or "users" not in response or "nodes" not in response["users"]:
            return {}

        # Convert to dictionary of ID -> LinearUser
        users = {}
        for user_obj in response["users"]["nodes"]:
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
        query {
            users {
                nodes {
                    id
                    email
                }
            }
        }
        """

        response = self._execute_query(query)

        if not response or "users" not in response or "nodes" not in response["users"]:
            return {}

        email_map = {user["id"]: user["email"] for user in response["users"]["nodes"]}

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
        query {
            users {
                nodes {
                    id
                    name
                    displayName
                }
            }
        }
        """

        response = self._execute_query(query)

        if not response or "users" not in response or "nodes" not in response["users"]:
            raise ValueError("No users found")

        # First, look for exact matches
        for user in response["users"]["nodes"]:
            if user["name"] == name or user["displayName"] == name:
                self._cache_set("user_id_by_name", name, user["id"])
                return user["id"]

        # Then, look for case-insensitive matches
        name_lower = name.lower()
        for user in response["users"]["nodes"]:
            if user["name"].lower() == name_lower or user["displayName"].lower() == name_lower:
                self._cache_set("user_id_by_name", name, user["id"])
                return user["id"]

        # Then, look for partial matches
        for user in response["users"]["nodes"]:
            if (
                    name_lower in user["name"].lower()
                    or name_lower in user["displayName"].lower()
            ):
                self._cache_set("user_id_by_name", name, user["id"])
                return user["id"]

        raise ValueError(f"No user found matching '{name}'")

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

    def invalidate_cache(self) -> None:
        """
        Invalidate all user-related caches.
        This should be called after any mutating operations.
        """
        self._cache_clear()
