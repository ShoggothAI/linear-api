"""
Issue-related domain models for Linear API.

This module defines models related to issues in the Linear API.
"""

from datetime import datetime
from typing import Optional, Dict, Union, List, Any, ClassVar

from pydantic import Field

from .base_domain import LinearModel
from .common_models import DocumentContent, Comment, Favorite, Template, ActorBot, ExternalUser
from .enums import LinearPriority, SLADayCountType, IntegrationService
from .project_models import LinearProject, ProjectMilestone, Cycle
from .team_models import LinearTeam, LinearState
from .user_models import LinearUser, LinearUserReference


class LinearLabel(LinearModel):
    """
    Represents a label in Linear.
    """

    linear_class_name: ClassVar[str] = "IssueLabel"
    known_extra_fields: ClassVar[List[str]] = ["issue_ids"]
    known_missing_fields: ClassVar[List[str]] = ["children", "issues", "team"]

    id: str
    name: str
    color: str

    archivedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    description: Optional[str] = None
    isGroup: Optional[bool] = None
    inheritedFrom: Optional[Dict[str, Any]] = None
    parent: Optional["LinearLabel"] = None
    creator: Optional[LinearUserReference] = None
    issue_ids: Optional[List[str]] = None


class LinearAttachment(LinearModel):
    """
    Represents an attachment in Linear.
    """

    linear_class_name: ClassVar[str] = "Attachment"
    known_extra_fields: ClassVar[List[str]] = ["issueId"]
    known_missing_fields: ClassVar[List[str]] = ["issue"]

    id: str  # Unique identifier for the attachment
    url: str  # URL or resource identifier for the attachment
    title: Optional[str] = None  # Title of the attachment
    subtitle: Optional[str] = None  # Subtitle or additional description
    metadata: Optional[Dict[str, Any]] = None  # Key-value metadata
    issueId: str  # ID of the issue this attachment is associated with
    createdAt: datetime  # Timestamp when the attachment was created
    updatedAt: datetime  # Timestamp when the attachment was last updated

    archivedAt: Optional[datetime] = None
    bodyData: Optional[Dict[str, Any]] = None
    groupBySource: Optional[bool] = None
    source: Optional[str] = None
    sourceType: Optional[str] = None

    creator: Optional[LinearUser] = None
    externalUserCreator: Optional[ExternalUser] = None


class LinearAttachmentInput(LinearModel):
    """
    Input for creating an attachment in Linear.
    """

    linear_class_name: ClassVar[str] = "AttachmentInput"

    url: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    issueId: str


class LinearIssue(LinearModel):
    """
    Represents a complete issue retrieved from Linear.
    """

    linear_class_name: ClassVar[str] = "Issue"
    known_extra_fields: ClassVar[List[str]] = ["parentId"]

    # Required fields
    id: str
    title: str
    url: str = Field(..., alias="url")
    state: LinearState
    priority: LinearPriority
    team: LinearTeam
    createdAt: datetime
    updatedAt: datetime
    number: int
    customerTicketCount: int

    # Optional fields
    description: Optional[str] = None
    assignee: Optional[LinearUser] = None
    project: Optional[LinearProject] = None
    labels: List[LinearLabel] = Field(default_factory=list)
    dueDate: Optional[datetime] = None
    parentId: Optional[str] = None
    archivedAt: Optional[datetime] = None
    estimate: Optional[int] = None
    branchName: Optional[str] = None
    attachments: List[LinearAttachment] = Field(default_factory=list)
    sortOrder: Optional[float] = None
    prioritySortOrder: Optional[float] = None
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    startedTriageAt: Optional[datetime] = None
    triagedAt: Optional[datetime] = None
    canceledAt: Optional[datetime] = None
    autoClosedAt: Optional[datetime] = None
    autoArchivedAt: Optional[datetime] = None
    slaStartedAt: Optional[datetime] = None
    slaMediumRiskAt: Optional[datetime] = None
    slaHighRiskAt: Optional[datetime] = None
    slaBreachesAt: Optional[datetime] = None
    slaType: Optional[str] = None
    addedToProjectAt: Optional[datetime] = None
    addedToCycleAt: Optional[datetime] = None
    addedToTeamAt: Optional[datetime] = None
    trashed: Optional[bool] = None
    snoozedUntilAt: Optional[datetime] = None
    suggestionsGeneratedAt: Optional[datetime] = None
    activitySummary: Optional[Dict[str, Any]] = None
    documentContent: Optional[DocumentContent] = None
    labelIds: Optional[List[str]] = None
    cycle: Optional[Cycle] = None
    projectMilestone: Optional[ProjectMilestone] = None
    lastAppliedTemplate: Optional[Template] = None
    recurringIssueTemplate: Optional[Template] = None
    previousIdentifiers: Optional[List[str]] = None
    creator: Optional[LinearUser] = None
    externalUserCreator: Optional[ExternalUser] = None
    snoozedBy: Optional[LinearUser] = None
    subIssueSortOrder: Optional[float] = None
    reactionData: Optional[Dict[str, Any]] = None
    priorityLabel: Optional[str] = None
    sourceComment: Optional[Comment] = None
    integrationSourceType: Optional[IntegrationService] = None
    botActor: Optional[ActorBot] = None
    favorite: Optional[Favorite] = None
    identifier: Optional[str] = None
    descriptionState: Optional[str] = None

    @property
    def parent(self) -> Optional["LinearIssue"]:
        """
        Get the parent issue of this issue.

        Returns:
            The parent LinearIssue or None if there is no parent
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get(self.parentId)
            except Exception as e:
                print(f"Error fetching parent issue {self.parentId}: {e}")
        return None

    @property
    def children(self) -> Dict[str, "LinearIssue"]:
        """
        Get the child issues of this issue.

        Returns:
            A dictionary mapping issue IDs to LinearIssue objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_children(self.id)
            except Exception as e:
                print(f"Error fetching child issues for {self.id}: {e}")
        return {}

    @property
    def comments(self) -> List[Comment]:
        """
        Get comments for this issue.

        Returns:
            A list of Comment objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_comments(self.id)
            except Exception as e:
                print(f"Error fetching comments for issue {self.id}: {e}")
        return []

    @property
    def history(self) -> List[Dict[str, Any]]:
        """
        Get the change history for this issue.

        Returns:
            A list of history items
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_history(self.id)
            except Exception as e:
                print(f"Error fetching history for issue {self.id}: {e}")
        return []

    @property
    def relations(self) -> List["IssueRelation"]:
        """
        Get relations for this issue.

        Returns:
            A list of issue relation objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_relations(self.id)
            except Exception as e:
                print(f"Error fetching relations for issue {self.id}: {e}")
        return []

    @property
    def inverseRelations(self) -> List["IssueRelation"]:
        """
        Get inverse relations for this issue.

        Returns:
            A list of issue relation objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_inverse_relations(self.id)
            except Exception as e:
                print(f"Error fetching inverse relations for issue {self.id}: {e}")
        return []

    @property
    def needs(self) -> List["CustomerNeedResponse"]:
        """
        Get customer needs associated with this issue.

        Returns:
            A list of CustomerNeedResponse objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_needs(self.id)
            except Exception as e:
                print(f"Error fetching needs for issue {self.id}: {e}")
        else:
            print(f"Warning: Cannot fetch needs, no manager reference available for issue {self.id}")
        return []

    @property
    def reactions(self) -> List["Reaction"]:
        """
        Get reactions to this issue.

        Returns:
            A list of reaction objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_reactions(self.id)
            except Exception as e:
                print(f"Error fetching reactions for issue {self.id}: {e}")
        return []

    @property
    def subscribers(self) -> List[LinearUser]:
        """
        Get subscribers to this issue.

        Returns:
            A list of LinearUser objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.issues.get_subscribers(self.id)
            except Exception as e:
                print(f"Error fetching subscribers for issue {self.id}: {e}")
        return []

    @property
    def metadata(self) -> Dict[str, Union[str, int, float]]:
        """
        Get the metadata for this issue from its attachments.

        Returns:
            A dictionary containing the issue's metadata
        """
        if self.attachments is not None:
            metadata_attachments = [
                a for a in self.attachments if "{" in a.title and "}" in a.title
            ]
            if metadata_attachments:
                return metadata_attachments[0].metadata or {}

        return {}


class LinearIssueInput(LinearModel):
    """
    Represents the input for creating a new issue in Linear.
    """

    linear_class_name: ClassVar[str] = "IssueCreateInput"

    # Required fields
    title: str
    teamName: str

    # Common optional fields
    description: Optional[str] = None
    priority: LinearPriority = LinearPriority.MEDIUM
    stateName: Optional[str] = None
    assigneeId: Optional[str] = None
    projectName: Optional[str] = None
    labelIds: Optional[List[str]] = None
    dueDate: Optional[datetime] = None
    parentId: Optional[str] = None
    estimate: Optional[int] = None
    descriptionData: Optional[Dict[str, Any]] = None
    subscriberIds: Optional[List[str]] = None
    cycleName: Optional[str] = None  # Will be converted to cycleId
    projectMilestoneName: Optional[str] = None  # Will be converted to projectMilestoneId
    templateName: Optional[str] = None  # Will be converted to templateId
    sortOrder: Optional[float] = None
    prioritySortOrder: Optional[float] = None
    subIssueSortOrder: Optional[float] = None
    displayIconUrl: Optional[str] = None
    preserveSortOrderOnCreate: Optional[bool] = None
    createdAt: Optional[datetime] = None
    slaBreachesAt: Optional[datetime] = None
    slaStartedAt: Optional[datetime] = None
    slaType: Optional[SLADayCountType] = None
    completedAt: Optional[datetime] = None

    # metadata will be auto-converted into an attachment
    metadata: Optional[Dict[str, Any]] = None


class LinearIssueUpdateInput(LinearModel):
    """
    Represents the input for updating an existing issue in Linear.
    All fields are optional since you only need to specify the fields you want to update.
    """

    linear_class_name: ClassVar[str] = "IssueUpdateInput"

    # Common fields
    title: Optional[str] = None
    description: Optional[str] = None
    teamName: Optional[str] = None
    priority: Optional[LinearPriority] = None
    stateName: Optional[str] = None
    assigneeId: Optional[str] = None
    projectName: Optional[str] = None
    labelIds: Optional[List[str]] = None
    dueDate: Optional[datetime] = None
    parentId: Optional[str] = None
    estimate: Optional[int] = None
    descriptionData: Optional[Dict[str, Any]] = None
    subscriberIds: Optional[List[str]] = None
    addedLabelIds: Optional[List[str]] = None
    removedLabelIds: Optional[List[str]] = None
    cycleName: Optional[str] = None  # Will be converted to cycleId
    projectMilestoneName: Optional[str] = None  # Will be converted to projectMilestoneId
    templateName: Optional[str] = None  # Will be converted to templateId
    sortOrder: Optional[float] = None
    prioritySortOrder: Optional[float] = None
    subIssueSortOrder: Optional[float] = None
    trashed: Optional[bool] = None
    slaBreachesAt: Optional[datetime] = None
    slaStartedAt: Optional[datetime] = None
    snoozedUntilAt: Optional[datetime] = None
    snoozedById: Optional[str] = None
    slaType: Optional[SLADayCountType] = None
    autoClosedByParentClosing: Optional[bool] = None

    # metadata will be auto-converted into an attachment
    metadata: Optional[Dict[str, Any]] = None


class IssueRelation(LinearModel):
    """Represents an issue relation in Linear"""
    linear_class_name: ClassVar[str] = "IssueRelation"

    id: str
    type: str
    relatedIssue: Optional[Dict[str, Any]] = None
    createdAt: datetime


class CustomerNeedResponse(LinearModel):
    """Customer need model matching the actual API response"""
    linear_class_name: ClassVar[str] = "CustomerNeed"

    id: str
    createdAt: datetime
    updatedAt: datetime
    archivedAt: Optional[datetime] = None
    priority: Optional[float] = None
    body: Optional[str] = None
    bodyData: Optional[str] = None
    url: Optional[str] = None
    creator: Optional[LinearUser] = None
