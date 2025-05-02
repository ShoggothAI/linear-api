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

        return LinearUser(**response["user"])

    def get_all(self) -> Dict[str, LinearUser]:
        """
        Get all users in the organization.

        Returns:
            A dictionary mapping user IDs to LinearUser objects
        """
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

        return users

    def get_email_map(self) -> Dict[str, str]:
        """
        Get a mapping of user IDs to their emails.

        Returns:
            A dictionary mapping user IDs to email addresses
        """
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

        return {user["id"]: user["email"] for user in response["users"]["nodes"]}

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
        # Get the email map
        email_map = self.get_email_map()

        # Invert the map (email -> id)
        id_map = {v: k for k, v in email_map.items()}

        if email in id_map:
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
        # Check if we have this cached
        if hasattr(self, '_user_name_cache'):
            if name in self._user_name_cache:
                return self._user_name_cache[name]
        else:
            self._user_name_cache = {}

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
                self._user_name_cache[name] = user["id"]
                return user["id"]

        # Then, look for case-insensitive matches
        name_lower = name.lower()
        for user in response["users"]["nodes"]:
            if user["name"].lower() == name_lower or user["displayName"].lower() == name_lower:
                self._user_name_cache[name] = user["id"]
                return user["id"]

        # Then, look for partial matches
        for user in response["users"]["nodes"]:
            if (
                    name_lower in user["name"].lower()
                    or name_lower in user["displayName"].lower()
            ):
                self._user_name_cache[name] = user["id"]
                return user["id"]

        raise ValueError(f"No user found matching '{name}'")

    def get_me(self) -> LinearUser:
        """
        Get the current user (based on the API key).

        Returns:
            A LinearUser object representing the current user
        """
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
        return self.get(response["viewer"]["id"])
