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
    known_missing_fields: ClassVar[List[str]] = [
        "assignedIssues",
        "createdIssues",
        "drafts",
        "issueDrafts",
        "teamMemberships",
        "teams"
    ]

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


class UserConnection(LinearModel):
    """Connection model for users"""
    linear_class_name: ClassVar[str] = "UserConnection"

    nodes: List[LinearUserReference] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None
