from typing import Optional, Dict, Union, List, Any
from datetime import datetime
from enum import Enum, StrEnum
from typing import List, Optional

from pydantic import BaseModel, Field


class LinearPriority(Enum):
    URGENT = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    NONE = 4


class SLADayCountType(StrEnum):
    """Enum for SLA day count types"""

    ALL = "all"
    ONLY_BUSINESS_DAYS = "onlyBusinessDays"


class LinearState(BaseModel):
    id: str
    name: str
    type: str
    color: str


class LinearLabel(BaseModel):
    id: str
    name: str
    color: str


class LinearUser(BaseModel):
    id: str
    name: str
    displayName: str
    email: str
    avatarUrl: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    archivedAt: Optional[datetime] = None


class LinearProject(BaseModel):
    id: str
    name: str
    description: Optional[str]


class LinearTeam(BaseModel):
    id: str
    name: str
    key: str
    description: Optional[str]


class LinearAttachmentInput(BaseModel):
    url: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    metadata: Optional[Dict[str, Union[str, int, float]]] = None
    issueId: str


class LinearAttachment(BaseModel):
    id: str  # Unique identifier for the attachment
    url: str  # URL or resource identifier for the attachment
    title: Optional[str]  # Title of the attachment
    subtitle: Optional[str]  # Subtitle or additional description
    metadata: Optional[
        Dict[str, Union[str, int, float]]
    ]  # Key-value metadata (can store JSON payloads)
    issueId: str  # ID of the issue this attachment is associated with
    createdAt: datetime  # Timestamp when the attachment was created
    updatedAt: datetime  # Timestamp when the attachment was last updated


class LinearIssueInput(BaseModel):
    """
    Represents the input for creating a new issue in Linear.
    """

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
    metadata: Optional[Dict[str, Union[str, int, float]]] = None


class LinearIssueUpdateInput(BaseModel):
    """
    Represents the input for updating an existing issue in Linear.
    All fields are optional since you only need to specify the fields you want to update.
    """

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
    metadata: Optional[Dict[str, Union[str, int, float]]] = None


class IntegrationService(StrEnum):
    """Enum for integration service types"""

    ASANA = "asana"
    FIGMA = "figma"
    GITHUB = "github"
    GITLAB = "gitlab"
    INTERCOM = "intercom"
    JIRA = "jira"
    NOTION = "notion"
    SLACK = "slack"
    ZENDESK = "zendesk"


class ActorBot(BaseModel):
    """Represents a bot actor in Linear"""

    id: str
    name: str


class Favorite(BaseModel):
    """Represents a user's favorite in Linear"""

    id: str
    createdAt: datetime
    updatedAt: datetime


class Comment(BaseModel):
    """Represents a comment in Linear"""

    id: str
    body: str
    createdAt: datetime
    updatedAt: datetime


class Cycle(BaseModel):
    """Represents a cycle in Linear"""

    id: str
    name: str
    number: int
    startsAt: datetime
    endsAt: datetime


class ProjectMilestone(BaseModel):
    """Represents a project milestone in Linear"""

    id: str
    name: str


class Template(BaseModel):
    """Represents a template in Linear"""

    id: str
    name: str


class ExternalUser(BaseModel):
    """Represents an external user in Linear"""

    id: str
    name: str
    email: str


class DocumentContent(BaseModel):
    """Represents document content in Linear"""

    id: str
    content: Optional[str] = None


class LinearIssue(BaseModel):
    """
    Represents a complete issue retrieved from Linear.
    """

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
    def metadata(self) -> Dict[str, Union[str, int, float]]:
        if self.attachments is not None:
            metadata_attachments = [
                a for a in self.attachments if "{" in a.title and "}" in a.title
            ]
            if metadata_attachments:
                return metadata_attachments[0].metadata or {}

        return {}
