from typing import Optional, Dict, Union, List, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum, StrEnum

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


# Generic connection type for pagination
T = TypeVar("T")


class Connection(BaseModel, Generic[T]):
    """Generic connection model for paginated results"""

    nodes: List[T] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class Organization(BaseModel):
    """Represents an organization in Linear"""

    id: str
    name: str
    # Add other fields as needed


class TeamMembership(BaseModel):
    """Represents a team membership in Linear"""

    id: str
    # Add other fields as needed


class Draft(BaseModel):
    """Represents a draft in Linear"""

    id: str
    # Add other fields as needed


class IssueDraft(BaseModel):
    """Represents an issue draft in Linear"""

    id: str
    # Add other fields as needed


class LinearState(BaseModel):
    id: str
    name: str
    type: str
    color: str


class LinearLabel(BaseModel):
    id: str
    name: str
    color: str


class LinearUserReference(BaseModel):
    """Simplified user reference for nested objects"""
    id: str
    name: str
    displayName: str
    email: str

    # Optional fields
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    avatarUrl: Optional[str] = None


class LinearUser(BaseModel):
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
    assignedIssues: Optional[Dict[str, Any]] = None  # Will be Connection[LinearIssue] when fully implemented
    createdIssues: Optional[Dict[str, Any]] = None   # Will be Connection[LinearIssue] when fully implemented
    drafts: Optional[Dict[str, Any]] = None          # Will be Connection[Draft] when fully implemented
    issueDrafts: Optional[Dict[str, Any]] = None     # Will be Connection[IssueDraft] when fully implemented
    organization: Optional[Organization] = None
    teamMemberships: Optional[Dict[str, Any]] = None  # Will be Connection[TeamMembership] when fully implemented
    teams: Optional[Dict[str, Any]] = None           # Will be Connection[LinearTeam] when fully implemented


# Forward declarations for connection classes
class Comment(BaseModel):
    """Represents a comment in Linear"""

    id: str
    body: str
    createdAt: datetime
    updatedAt: datetime


# For Project-related connections
class CommentConnection(BaseModel):
    """Connection model for comments"""
    nodes: List[Comment] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class DocumentConnection(BaseModel):
    """Connection model for documents"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class EntityExternalLinkConnection(BaseModel):
    """Connection model for external links"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class ProjectHistoryConnection(BaseModel):
    """Connection model for project history"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class InitiativeConnection(BaseModel):
    """Connection model for initiatives"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class IntegrationsSettings(BaseModel):
    """Represents integration settings"""
    id: str


class ProjectRelationConnection(BaseModel):
    """Connection model for project relations"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class IssueConnection(BaseModel):
    """Connection model for issues"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class ProjectLabelConnection(BaseModel):
    """Connection model for project labels"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class UserConnection(BaseModel):
    """Connection model for users"""
    nodes: List[LinearUserReference] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class CustomerNeedConnection(BaseModel):
    """Connection model for customer needs"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


# Forward declaration for ProjectMilestoneConnection
class ProjectMilestone(BaseModel):
    """Represents a project milestone in Linear"""

    id: str
    name: str


class ProjectMilestoneConnection(BaseModel):
    """Connection model for project milestones"""
    nodes: List[ProjectMilestone] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    """Represents a project update"""
    id: str


class ProjectUpdateConnection(BaseModel):
    """Connection model for project updates"""
    nodes: List[ProjectUpdate] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


# Forward declaration for TeamConnection
class LinearTeam(BaseModel):
    """Represents a team in Linear"""
    id: str
    name: str
    key: str
    description: Optional[str] = None


class TeamConnection(BaseModel):
    """Connection model for teams"""
    nodes: List[LinearTeam] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class TimelessDate(BaseModel):
    """Represents a date without time"""
    year: int
    month: int
    day: int


class DateResolutionType(StrEnum):
    """Enum for date resolution types"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


class FrequencyResolutionType(StrEnum):
    """Enum for frequency resolution types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ProjectUpdateHealthType(StrEnum):
    """Enum for project update health types"""
    ON_TRACK = "onTrack"
    AT_RISK = "atRisk"
    OFF_TRACK = "offTrack"


class ProjectStatusType(StrEnum):
    """Enum for project status types"""
    PLANNED = "planned"
    BACKLOG = "backlog"
    STARTED = "started"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ProjectStatus(BaseModel):
    """Represents a project status in Linear"""
    type: ProjectStatusType


class Day(StrEnum):
    """Enum for days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class DocumentContent(BaseModel):
    """Represents document content in Linear"""

    id: str
    content: Optional[str] = None


class Favorite(BaseModel):
    """Represents a user's favorite in Linear"""

    id: str
    createdAt: datetime
    updatedAt: datetime


class Template(BaseModel):
    """Represents a template in Linear"""

    id: str
    name: str


class LinearProject(BaseModel):
    """Represents a complete project retrieved from Linear."""

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

    # Fields with unknown types in the API (marked as None in the schema validator)
    completedIssueCountHistory: Optional[Dict[str, Any]] = None
    completedScopeHistory: Optional[Dict[str, Any]] = None
    inProgressScopeHistory: Optional[Dict[str, Any]] = None
    issueCountHistory: Optional[Dict[str, Any]] = None
    scopeHistory: Optional[Dict[str, Any]] = None


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


class Cycle(BaseModel):
    """Represents a cycle in Linear"""

    id: str
    name: str
    number: int
    startsAt: datetime
    endsAt: datetime


class ExternalUser(BaseModel):
    """Represents an external user in Linear"""

    id: str
    name: str
    email: str


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
