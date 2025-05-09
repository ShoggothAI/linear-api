"""
Team-related domain models for Linear API.

This module defines models related to teams in the Linear API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, ClassVar, List, Union

from pydantic import Field

from . import Template, IntegrationsSettings, Organization
from .base_domain import LinearModel


class LinearState(LinearModel):
    """
    Represents a workflow state in Linear.
    """
    linear_class_name: ClassVar[str] = "WorkflowState"
    known_extra_fields: ClassVar[List[str]] = ["issue_ids"]
    known_missing_fields: ClassVar[List[str]] = ["team", "issues"]

    id: str
    name: str
    type: str
    color: str

    archivedAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    description: Optional[str] = None
    position: Optional[float] = None
    inheritedFrom: Optional[Dict[str, Any]] = None
    issue_ids: Optional[List[str]] = None


class LinearTeam(LinearModel):
    """
    Represents a team in Linear.
    """
    linear_class_name: ClassVar[str] = "Team"
    known_extra_fields: ClassVar[List[str]] = ["parentId"]
    known_missing_fields: ClassVar[List[str]] = [
        "activeCycle", "children", "cycles", "issues", "labels", "members",
        "memberships", "projects", "templates", "webhooks", "parent",
        "facets", "gitAutomationStates", "membership", "triageResponsibility"
    ]

    id: str
    name: str
    key: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    parentId: Optional[str] = None

    archivedAt: Optional[datetime] = None
    displayName: Optional[str] = None
    private: Optional[bool] = None
    timezone: Optional[str] = None

    posts: Optional[List[Any]] = None
    progressHistory: Optional[List[Any]] = None
    upcomingCycleCount: Optional[int] = None

    # Configuration parameters
    autoArchivePeriod: Optional[int] = None
    autoCloseChildIssues: Optional[bool] = None
    autoCloseParentIssues: Optional[bool] = None
    autoClosePeriod: Optional[int] = None
    autoCloseStateId: Optional[str] = None

    # Cycle parameters
    cycleDuration: Optional[int] = None
    cycleStartDay: Optional[Union[str, int]] = None
    cyclesEnabled: Optional[bool] = None
    cycleCooldownTime: Optional[int] = None
    cycleCalenderUrl: Optional[str] = None
    cycleLockToActive: Optional[bool] = None
    cycleIssueAutoAssignCompleted: Optional[bool] = None
    cycleIssueAutoAssignStarted: Optional[bool] = None

    # Estimation parameters
    defaultIssueEstimate: Optional[int] = None
    issueEstimationType: Optional[str] = None
    issueEstimationAllowZero: Optional[bool] = None
    issueEstimationExtended: Optional[bool] = None
    inheritIssueEstimation: Optional[bool] = None

    # Other settings
    inviteHash: Optional[str] = None
    issueCount: Optional[int] = None
    joinByDefault: Optional[bool] = None
    groupIssueHistory: Optional[bool] = None
    inheritWorkflowStatuses: Optional[bool] = None
    setIssueSortOrderOnStateChange: Optional[Union[bool, str]] = None
    requirePriorityToLeaveTriage: Optional[bool] = None
    triageEnabled: Optional[bool] = None

    # Default templates and states
    defaultIssueState: Optional[LinearState] = None
    defaultProjectTemplate: Optional[Template] = None
    defaultTemplateForMembers: Optional[Template] = None
    defaultTemplateForNonMembers: Optional[Template] = None
    markedAsDuplicateWorkflowState: Optional[LinearState] = None
    triageIssueState: Optional[LinearState] = None

    # SCIM Parameters
    scimGroupName: Optional[str] = None
    scimManaged: Optional[bool] = None

    # AI parameters
    aiThreadSummariesEnabled: Optional[bool] = None

    # Integration and progress settings
    currentProgress: Optional[Dict[str, Any]] = None
    integrationsSettings: Optional[IntegrationsSettings] = None

    # Связанные объекты
    organization: Optional[Organization] = None
    states: Optional[Dict[str, Any]] = None  # This can be replaced with a typed Connection

class TeamConnection(LinearModel):
    """
    Connection model for teams.
    """
    linear_class_name: ClassVar[str] = "TeamConnection"

    nodes: List[LinearTeam] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None
