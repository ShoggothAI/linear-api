"""
Project-related domain models for Linear API.

This module defines models related to projects in the Linear API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, ClassVar, List

from pydantic import Field, BaseModel

from .base_domain import LinearModel
from .common_models import (
    CommentConnection, DocumentConnection, EntityExternalLinkConnection,
    DocumentContent, Favorite, Template, TimelessDate, IntegrationsSettings
)
from .enums import (
    DateResolutionType, Day, FrequencyResolutionType,
    ProjectStatusType, ProjectUpdateHealthType
)
from .team_models import TeamConnection
from .user_models import LinearUserReference, UserConnection, LinearUser


class ProjectStatus(LinearModel):
    """
    Represents a project status in Linear.
    """
    linear_class_name: ClassVar[str] = "ProjectStatus"

    type: ProjectStatusType


class ProjectMilestone(LinearModel):
    """
    Represents a project milestone in Linear.
    """
    linear_class_name: ClassVar[str] = "ProjectMilestone"

    id: str
    name: str


class ProjectMilestoneConnection(LinearModel):
    """
    Connection model for project milestones.
    """
    linear_class_name: ClassVar[str] = "ProjectMilestoneConnection"

    nodes: List[ProjectMilestone] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class ProjectUpdate(LinearModel):
    """
    Represents a project update.
    """
    linear_class_name: ClassVar[str] = "ProjectUpdate"

    id: str


class ProjectUpdateConnection(LinearModel):
    """
    Connection model for project updates.
    """
    linear_class_name: ClassVar[str] = "ProjectUpdateConnection"

    nodes: List[ProjectUpdate] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class ProjectHistoryConnection(LinearModel):
    """
    Connection model for project history.
    """
    linear_class_name: ClassVar[str] = "ProjectHistoryConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class InitiativeConnection(LinearModel):
    """
    Connection model for initiatives.
    """
    linear_class_name: ClassVar[str] = "InitiativeConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class ProjectRelationConnection(LinearModel):
    """
    Connection model for project relations.
    """
    linear_class_name: ClassVar[str] = "ProjectRelationConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class IssueConnection(LinearModel):
    """
    Connection model for issues.
    """
    linear_class_name: ClassVar[str] = "IssueConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class ProjectLabelConnection(LinearModel):
    """
    Connection model for project labels.
    """
    linear_class_name: ClassVar[str] = "ProjectLabelConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class CustomerNeedConnection(LinearModel):
    """
    Connection model for customer needs.
    """
    linear_class_name: ClassVar[str] = "CustomerNeedConnection"

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class LinearProject(LinearModel):
    """
    Represents a complete project retrieved from Linear.
    """
    linear_class_name: ClassVar[str] = "Project"
    known_extra_fields: ClassVar[List[str]] = []
    known_missing_fields: ClassVar[List[str]] = [
        "members",
        "projectMilestones",
        "comments",
        "issues",
        "projectUpdates",
        "relations",
        "teams",
        "documents",
        "externalLinks",
        "history",
        "initiatives",
        "labels",
        "needs"
    ]

    # Required fields
    id: str
    name: str
    createdAt: datetime
    updatedAt: datetime
    slugId: str
    url: str
    color: str
    priority: int
    priorityLabel: str
    prioritySortOrder: float
    sortOrder: float
    progress: float
    status: ProjectStatus
    scope: float
    frequencyResolution: FrequencyResolutionType

    # Optional fields
    description: Optional[str] = None
    archivedAt: Optional[datetime] = None
    autoArchivedAt: Optional[datetime] = None
    canceledAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    content: Optional[str] = None
    contentState: Optional[str] = None
    health: Optional[ProjectUpdateHealthType] = None
    healthUpdatedAt: Optional[datetime] = None
    icon: Optional[str] = None
    startDate: Optional[TimelessDate] = None
    startDateResolution: Optional[DateResolutionType] = None
    startedAt: Optional[datetime] = None
    targetDate: Optional[TimelessDate] = None
    targetDateResolution: Optional[DateResolutionType] = None
    trashed: Optional[bool] = None
    updateReminderFrequency: Optional[float] = None
    updateReminderFrequencyInWeeks: Optional[float] = None
    updateRemindersDay: Optional[Day] = None
    updateRemindersHour: Optional[float] = None
    projectUpdateRemindersPausedUntilAt: Optional[datetime] = None

    # Complex fields
    convertedFromIssue: Optional[Dict[str, Any]] = None
    creator: Optional[LinearUserReference] = None
    currentProgress: Optional[Dict[str, Any]] = None
    favorite: Optional[Favorite] = None
    integrationsSettings: Optional[IntegrationsSettings] = None
    inverseRelations: Optional[ProjectRelationConnection] = None
    labelIds: Optional[List[str]] = None
    lastAppliedTemplate: Optional[Template] = None
    lastUpdate: Optional[ProjectUpdate] = None
    lead: Optional[LinearUserReference] = None
    progressHistory: Optional[Dict[str, Any]] = None
    relations: Optional[ProjectRelationConnection] = None

    # Fields with unknown types in the API
    completedIssueCountHistory: Optional[Dict[str, Any]] = None
    completedScopeHistory: Optional[Dict[str, Any]] = None
    inProgressScopeHistory: Optional[Dict[str, Any]] = None
    issueCountHistory: Optional[Dict[str, Any]] = None
    scopeHistory: Optional[Dict[str, Any]] = None


class Cycle(BaseModel):
    """Represents a cycle in Linear"""

    id: str
    name: Optional[str] = None
    number: int
    startsAt: datetime
    endsAt: datetime


class CustomerNeed(LinearModel):
    """
    Represents a customer need in Linear.
    """
    linear_class_name: ClassVar[str] = "CustomerNeed"

    id: str
    createdAt: datetime
    updatedAt: datetime
    archivedAt: Optional[datetime] = None
    customer: Optional[Dict[str, Any]] = None
    issue: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None
    comment: Optional[Dict[str, Any]] = None
    attachment: Optional[Dict[str, Any]] = None
    projectAttachment: Optional[Dict[str, Any]] = None
    priority: Optional[float] = None
    body: Optional[str] = None
    bodyData: Optional[str] = None
    creator: Optional[LinearUser] = None
    url: Optional[str] = None


class Initiative(LinearModel):
    """
    Represents an initiative in Linear.
    """
    linear_class_name: ClassVar[str] = "Initiative"

    id: str
    name: str
    description: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class ProjectRelation(LinearModel):
    """Represents a relation between projects."""
    linear_class_name: ClassVar[str] = "ProjectRelation"

    id: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    archivedAt: Optional[datetime] = None
    type: str
    project: Optional[Dict[str, Any]] = None
    projectMilestone: Optional[Dict[str, Any]] = None
    anchorType: Optional[str] = None
    relatedProject: Optional[Dict[str, Any]] = None
    relatedProjectMilestone: Optional[Dict[str, Any]] = None
    relatedAnchorType: Optional[str] = None
    user: Optional[LinearUser] = None


class ProjectHistory(LinearModel):
    """Represents a history entry for a project."""
    linear_class_name: ClassVar[str] = "ProjectHistory"

    id: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    archivedAt: Optional[datetime] = None
    entries: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None