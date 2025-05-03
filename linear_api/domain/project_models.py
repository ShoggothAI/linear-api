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
from .user_models import LinearUserReference, UserConnection


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
    comments: Optional[CommentConnection] = None
    convertedFromIssue: Optional[Dict[str, Any]] = None
    creator: Optional[LinearUserReference] = None
    currentProgress: Optional[Dict[str, Any]] = None
    documentContent: Optional[DocumentContent] = None
    documents: Optional[DocumentConnection] = None
    externalLinks: Optional[EntityExternalLinkConnection] = None
    favorite: Optional[Favorite] = None
    history: Optional[ProjectHistoryConnection] = None
    initiatives: Optional[InitiativeConnection] = None
    integrationsSettings: Optional[IntegrationsSettings] = None
    inverseRelations: Optional[ProjectRelationConnection] = None
    issues: Optional[IssueConnection] = None
    labelIds: Optional[List[str]] = None
    labels: Optional[ProjectLabelConnection] = None
    lastAppliedTemplate: Optional[Template] = None
    lastUpdate: Optional[ProjectUpdate] = None
    lead: Optional[LinearUserReference] = None
    members: Optional[UserConnection] = None
    needs: Optional[CustomerNeedConnection] = None
    progressHistory: Optional[Dict[str, Any]] = None
    projectMilestones: Optional[ProjectMilestoneConnection] = None
    projectUpdates: Optional[ProjectUpdateConnection] = None
    relations: Optional[ProjectRelationConnection] = None
    teams: Optional[TeamConnection] = None

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
