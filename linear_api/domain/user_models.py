"""
User-related domain models for Linear API.

This module defines models related to users in the Linear API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, ClassVar, List

from pydantic import Field

from .base_domain import LinearModel
from .common_models import Organization


class LinearUserReference(LinearModel):
    """Simplified user reference for nested objects"""
    linear_class_name: ClassVar[str] = "User"

    id: str
    name: str
    displayName: str
    email: Optional[str] = None

    # Optional fields
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    avatarUrl: Optional[str] = None


class LinearUser(LinearModel):
    """
    Represents a complete user in Linear.
    """
    linear_class_name: ClassVar[str] = "User"

    # Required fields
    id: str
    name: str
    displayName: str
    email: str
    createdAt: datetime
    updatedAt: datetime

    # Optional fields from original model
    avatarUrl: Optional[str] = None
    archivedAt: Optional[datetime] = None

    # Additional fields from API
    active: bool = False
    admin: bool = False
    app: bool = False
    avatarBackgroundColor: Optional[str] = None
    calendarHash: Optional[str] = None
    createdIssueCount: int = 0
    description: Optional[str] = None
    disableReason: Optional[str] = None
    guest: bool = False
    initials: Optional[str] = None
    inviteHash: Optional[str] = None
    isMe: bool = False
    lastSeen: Optional[datetime] = None
    statusEmoji: Optional[str] = None
    statusLabel: Optional[str] = None
    statusUntilAt: Optional[datetime] = None
    timezone: Optional[str] = None
    url: Optional[str] = None

    # Complex fields with their models
    organization: Optional[Organization] = None

    # Property getters for missing fields using manager methods

    @property
    def assignedIssues(self) -> Dict[str, "LinearIssue"]:
        """
        Get issues assigned to this user.

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.users.get_assigned_issues(self.id)
            except Exception as e:
                print(f"Error fetching assigned issues for user {self.id}: {e}")
        return {}

    @property
    def createdIssues(self) -> List[Dict[str, Any]]:
        """
        Get issues created by this user.

        Returns:
            A list of issue data dictionaries
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.users.get_created_issues(self.id)
            except Exception as e:
                print(f"Error fetching created issues for user {self.id}: {e}")
        return []

    @property
    def drafts(self) -> List["Draft"]:
        """
        Get document drafts created by this user.

        Returns:
            A list of Draft objects for the user
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.users.get_drafts(self.id)
            except Exception as e:
                print(f"Error fetching drafts for user {self.id}: {e}")
        return []

    @property
    def issueDrafts(self) -> List["IssueDraft"]:
        """
        Get issue drafts created by this user.

        Returns:
            A list of IssueDraft objects for the user
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.users.get_issue_drafts(self.id)
            except Exception as e:
                print(f"Error fetching issue drafts for user {self.id}: {e}")
        return []

    @property
    def teamMemberships(self) -> List[Dict[str, Any]]:
        """
        Get team memberships for this user.

        Returns:
            A list of team membership data
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.users.get_team_memberships(self.id)
            except Exception as e:
                print(f"Error fetching team memberships for user {self.id}: {e}")
        return []

    @property
    def teams(self) -> List["LinearTeam"]:
        """
        Get teams that this user is a member of.

        Returns:
            A list of LinearTeam objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.users.get_teams(self.id)
            except Exception as e:
                print(f"Error fetching teams for user {self.id}: {e}")
        return []


class UserConnection(LinearModel):
    """Connection model for users"""
    linear_class_name: ClassVar[str] = "UserConnection"

    nodes: List[LinearUserReference] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class Reaction(LinearModel):
    """Represents a reaction in Linear"""
    linear_class_name: ClassVar[str] = "Reaction"

    id: str
    emoji: str
    user: Optional[LinearUserReference] = None
    createdAt: datetime
