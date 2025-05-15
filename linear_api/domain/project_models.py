"""
Project-related domain models for Linear API.

This module defines models related to projects in the Linear API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, ClassVar, List

from pydantic import Field, BaseModel

from .base_domain import LinearModel
from .common_models import (
    Favorite, Template, TimelessDate, IntegrationsSettings,
    Comment, Document, EntityExternalLink
)
from .enums import (
    DateResolutionType, Day, FrequencyResolutionType,
    ProjectStatusType, ProjectUpdateHealthType
)
from .team_models import LinearTeam
from .user_models import LinearUserReference, LinearUser


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


class DocumentContent(LinearModel):
    """Represents document content in Linear"""
    linear_class_name: ClassVar[str] = "DocumentContent"

    id: str
    content: Optional[str] = None
    contentState: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    archivedAt: Optional[datetime] = None
    restoredAt: Optional[datetime] = None


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

    # Fields with unknown types in the API
    completedIssueCountHistory: Optional[Dict[str, Any]] = None
    completedScopeHistory: Optional[Dict[str, Any]] = None
    inProgressScopeHistory: Optional[Dict[str, Any]] = None
    issueCountHistory: Optional[Dict[str, Any]] = None
    scopeHistory: Optional[Dict[str, Any]] = None

    documentContent: Optional[DocumentContent] = None

    # Property getters for missing fields using manager methods

    @property
    def members(self) -> List[LinearUser]:
        """
        Get members of this project.

        Returns:
            A list of LinearUser objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_members(self.id)
            except Exception as e:
                print(f"Error fetching members for project {self.id}: {e}")
        return []

    @property
    def projectMilestones(self) -> List[ProjectMilestone]:
        """
        Get milestones for this project.

        Returns:
            A list of ProjectMilestone objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_milestones(self.id)
            except Exception as e:
                print(f"Error fetching milestones for project {self.id}: {e}")
        return []

    @property
    def comments(self) -> List[Comment]:
        """
        Get comments for this project.

        Returns:
            A list of Comment objects
        """
        if hasattr(self, "_client") and self._client:
            try:
               return self._client.projects.get_comments(self.id)
            except Exception as e:
                print(f"Error fetching comments for project {self.id}: {e}")
        return []

    @property
    def issues(self) -> List[Dict[str, Any]]:
        """
        Get issues for this project.

        Returns:
            A list of issue data dictionaries
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_issues(self.id)
            except Exception as e:
                print(f"Error fetching issues for project {self.id}: {e}")
        return []

    @property
    def projectUpdates(self) -> List[ProjectUpdate]:
        """
        Get updates for this project.

        Returns:
            A list of ProjectUpdate objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_project_updates(self.id)
            except Exception as e:
                print(f"Error fetching updates for project {self.id}: {e}")
        return []

    @property
    def relations(self) -> List["ProjectRelation"]:
        """
        Get relations for this project.

        Returns:
            A list of ProjectRelation objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_relations(self.id)
            except Exception as e:
                print(f"Error fetching relations for project {self.id}: {e}")
        return []

    @property
    def teams(self) -> List[LinearTeam]:
        """
        Get teams associated with this project.

        Returns:
            A list of LinearTeam objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_teams(self.id)
            except Exception as e:
                print(f"Error fetching teams for project {self.id}: {e}")
        return []

    @property
    def documents(self) -> List[Document]:
        """
        Get documents associated with this project.

        Returns:
            A list of Document objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_documents(self.id)
            except Exception as e:
                print(f"Error fetching documents for project {self.id}: {e}")
        return []

    @property
    def externalLinks(self) -> List[EntityExternalLink]:
        """
        Get external links associated with this project.

        Returns:
            A list of EntityExternalLink objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_external_links(self.id)
            except Exception as e:
                print(f"Error fetching external links for project {self.id}: {e}")
        return []

    @property
    def history(self) -> List["ProjectHistory"]:
        """
        Get the history of this project.

        Returns:
            A list of ProjectHistory objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_history(self.id)
            except Exception as e:
                print(f"Error fetching history for project {self.id}: {e}")
        return []

    @property
    def initiatives(self) -> List[Dict[str, Any]]:
        """
        Get initiatives associated with this project.

        Returns:
            A list of initiative data dictionaries
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_initiatives(self.id)
            except Exception as e:
                print(f"Error fetching initiatives for project {self.id}: {e}")
        return []

    @property
    def labels(self) -> List["LinearLabel"]:
        """
        Get labels associated with this project.

        Returns:
            A list of LinearLabel objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_labels(self.id)
            except Exception as e:
                print(f"Error fetching labels for project {self.id}: {e}")
        return []

    @property
    def needs(self) -> List["CustomerNeed"]:
        """
        Get customer needs associated with this project.

        Returns:
            A list of CustomerNeed objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.projects.get_needs(self.id)
            except Exception as e:
                print(f"Error fetching needs for project {self.id}: {e}")
        return []


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
