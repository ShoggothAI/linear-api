"""
Common domain models for Linear API.

This module defines common utility models that are used across multiple resources.
"""

from datetime import datetime
from typing import Optional, Dict, Any, ClassVar, List

from pydantic import Field

from .base_domain import LinearModel


class Organization(LinearModel):
    """Represents an organization in Linear"""
    linear_class_name: ClassVar[str] = "Organization"

    id: str
    name: str


class Comment(LinearModel):
    """Represents a comment in Linear"""
    linear_class_name: ClassVar[str] = "Comment"

    id: str
    body: str
    createdAt: datetime
    updatedAt: datetime


class CommentConnection(LinearModel):
    """Connection model for comments"""
    linear_class_name: ClassVar[str] = "CommentConnection"

    nodes: List[Comment] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class DocumentContent(LinearModel):
    """Represents document content in Linear"""
    linear_class_name: ClassVar[str] = "DocumentContent"

    id: str
    content: Optional[str] = None


class DocumentConnection(LinearModel):
    """Connection model for documents"""
    linear_class_name: ClassVar[str] = "DocumentConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class EntityExternalLinkConnection(LinearModel):
    """Connection model for external links"""
    linear_class_name: ClassVar[str] = "EntityExternalLinkConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class Favorite(LinearModel):
    """Represents a user's favorite in Linear"""
    linear_class_name: ClassVar[str] = "Favorite"

    id: str
    createdAt: datetime
    updatedAt: datetime


class Template(LinearModel):
    """Represents a template in Linear"""
    linear_class_name: ClassVar[str] = "Template"

    id: str
    name: str


class TimelessDate(LinearModel):
    """Represents a date without time"""
    linear_class_name: ClassVar[str] = "TimelessDate"

    year: int
    month: int
    day: int


class IntegrationsSettings(LinearModel):
    """Represents integration settings"""
    linear_class_name: ClassVar[str] = "IntegrationsSettings"

    id: str


class TeamMembership(LinearModel):
    """Represents a team membership in Linear"""
    linear_class_name: ClassVar[str] = "TeamMembership"

    id: str


class Draft(LinearModel):
    """Represents a draft in Linear"""
    linear_class_name: ClassVar[str] = "Draft"

    id: str


class IssueDraft(LinearModel):
    """Represents an issue draft in Linear"""
    linear_class_name: ClassVar[str] = "IssueDraft"

    id: str


class ActorBot(LinearModel):
    """Represents a bot actor in Linear"""
    linear_class_name: ClassVar[str] = "ActorBot"

    id: str
    name: str


class ExternalUser(LinearModel):
    """Represents an external user in Linear"""
    linear_class_name: ClassVar[str] = "ExternalUser"

    id: str
    name: str
    email: str


class Document(LinearModel):
    """
    Represents a document in Linear.
    """
    linear_class_name: ClassVar[str] = "Document"

    id: str
    title: Optional[str] = None
    icon: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class EntityExternalLink(LinearModel):
    """
    Represents an external link for an entity in Linear.
    """
    linear_class_name: ClassVar[str] = "EntityExternalLink"

    id: str
    url: str
    label: Optional[str] = None
    createdAt: datetime
