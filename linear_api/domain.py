from typing import Optional, Dict, Union, List
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class LinearPriority(Enum):
    URGENT = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    NONE = 4


class LinearState(BaseModel):
    id: str
    name: str
    type: str
    color: str


class LinearLabel(BaseModel):
    id: str
    name: str
    color: str


class LinearBasicUser(BaseModel):
    id: str
    name: str
    email: str
    displayName: str


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

    title: str
    description: Optional[str] = None
    teamName: str
    priority: LinearPriority = LinearPriority.MEDIUM
    stateName: Optional[str] = None
    assigneeId: Optional[str] = None
    projectName: Optional[str] = None
    labelIds: Optional[List[str]] = None
    dueDate: Optional[datetime] = None
    parentId: Optional[str] = None
    # metadata will be auto-converted into an attachment
    metadata: Optional[Dict[str, Union[str, int, float]]] = None


class LinearIssue(BaseModel):
    """
    Represents a complete issue retrieved from Linear.
    """

    id: str
    title: str
    description: Optional[str] = None
    url: str = Field(..., alias="url")
    state: LinearState
    priority: LinearPriority
    assignee: Optional[LinearBasicUser] = None
    team: LinearTeam
    project: Optional[LinearProject] = None
    labels: List[LinearLabel] = Field(default_factory=list)
    dueDate: Optional[datetime] = None
    parentId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    archivedAt: Optional[datetime] = None
    number: int
    estimate: Optional[int] = None
    branchName: Optional[str] = None
    customerTicketCount: int
    attachments: List[LinearAttachment] = Field(default_factory=list)

    @property
    def metadata(self) -> Dict[str, Union[str, int, float]]:
        if self.attachments is not None:
            metadata_attachments = [
                a for a in self.attachments if "{" in a.title and "}" in a.title
            ]
            if metadata_attachments:
                return metadata_attachments[0].metadata or {}

        return {}
