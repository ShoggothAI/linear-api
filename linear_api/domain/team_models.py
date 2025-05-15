"""
Team-related domain models for Linear API.

This module defines models related to teams in the Linear API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, ClassVar, List, Union

from pydantic import Field

from . import Template, IntegrationsSettings, Organization
from .base_domain import LinearModel
from .user_models import LinearUser


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


class TeamMembership(LinearModel):
    """
    Represents a team membership in Linear.

    [ALPHA] The membership of the given user in the team.
    """
    linear_class_name: ClassVar[str] = "TeamMembership"

    id: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    archivedAt: Optional[datetime] = None
    owner: Optional[bool] = None
    sortOrder: Optional[float] = None
    user: Optional[LinearUser] = None
    team: Optional["LinearTeam"] = None


class LinearTeam(LinearModel):
    """
    Represents a team in Linear.
    """
    linear_class_name: ClassVar[str] = "Team"
    known_extra_fields: ClassVar[List[str]] = ["parentId"]
    # membership: TeamMembership
    # memberships: TeamMembershipConnection
    # facets: None Description: [Internal] Facets associated with the team.
    # gitAutomationStates: GitAutomationStateConnection
    #   Description: The Git automation states for the team
    # known_missing_fields: ClassVar[List[str]] = [
    #     "membership", "memberships", "facets", "gitAutomationStates",
    # ]

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

    # Related objects
    organization: Optional[Organization] = None
    states: Optional[Dict[str, Any]] = None  # This can be replaced with a typed Connection

    memberships: Optional[Dict[str, Any]] = None
    facets: Optional[List[Dict[str, Any]]] = None
    gitAutomationStates: Optional[Dict[str, Any]] = None

    # Property getters for missing fields using manager methods

    @property
    def activeCycle(self) -> Optional[Dict[str, Any]]:
        """
        Get the active cycle for this team.

        Returns:
            The active cycle data or None if no active cycle
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_active_cycle(self.id)
            except Exception as e:
                print(f"Error fetching active cycle for team {self.id}: {e}")
        return None

    @property
    def children(self) -> List["LinearTeam"]:
        """
        Get child teams for this team.

        Returns:
            A list of LinearTeam objects that are children of this team
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_children(self.id)
            except Exception as e:
                print(f"Error fetching child teams for team {self.id}: {e}")
        return []

    @property
    def cycles(self) -> List[Dict[str, Any]]:
        """
        Get cycles for this team.

        Returns:
            A list of cycle data
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_cycles(self.id)
            except Exception as e:
                print(f"Error fetching cycles for team {self.id}: {e}")
        return []

    @property
    def issues(self) -> List[Dict[str, Any]]:
        """
        Get issues for this team.

        Returns:
            A list of issue data dictionaries
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_issues(self.id)
            except Exception as e:
                print(f"Error fetching issues for team {self.id}: {e}")
        return []

    @property
    def labels(self) -> List["LinearLabel"]:
        """
        Get labels for this team.

        Returns:
            A list of LinearLabel objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_labels(self.id)
            except Exception as e:
                print(f"Error fetching labels for team {self.id}: {e}")
        return []

    @property
    def members(self) -> List[LinearUser]:
        """
        Get members of this team.

        Returns:
            A list of LinearUser objects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_members(self.id)
            except Exception as e:
                print(f"Error fetching members for team {self.id}: {e}")
        return []

    @property
    def projects(self) -> Dict[str, "LinearProject"]:
        """
        Get projects for this team.

        Returns:
            A dictionary containing the team's projects
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_projects(self.id)
            except Exception as e:
                print(f"Error fetching projects for team {self.id}: {e}")
        return {}

    @property
    def templates(self) -> List[Dict[str, Any]]:
        """
        Get templates for this team.

        Returns:
            A list of template data
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_templates(self.id)
            except Exception as e:
                print(f"Error fetching templates for team {self.id}: {e}")
        return []

    @property
    def webhooks(self) -> List[Dict[str, Any]]:
        """
        Get webhooks for this team.

        Returns:
            A list of webhook data
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_webhooks(self.id)
            except Exception as e:
                print(f"Error fetching webhooks for team {self.id}: {e}")
        return []

    @property
    def parent(self) -> Optional["LinearTeam"]:
        """
        Get the parent team of this team.

        Returns:
            The parent LinearTeam object or None if the team has no parent
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_parent(self.id)
            except Exception as e:
                print(f"Error fetching parent team for team {self.id}: {e}")
        return None

    @property
    def triageResponsibility(self) -> Optional["TriageResponsibility"]:
        """
        Get triage responsibility data for this team.

        Returns:
            Triage responsibility data or None if not available
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_triage_responsibility(self.id)
            except Exception as e:
                print(f"Error fetching triage responsibility for team {self.id}: {e}")
        return None

    @property
    def membership(self) -> Optional[TeamMembership]:
        """
        Get the membership of the current user in this team.

        Returns:
            The TeamMembership object or None if not found or no current user
        """
        if hasattr(self, "_client") and self._client:
            try:
                return self._client.teams.get_membership(self.id)
            except Exception as e:
                print(f"Error fetching membership for team {self.id}: {e}")
        return None


class TeamConnection(LinearModel):
    """
    Connection model for teams.
    """
    linear_class_name: ClassVar[str] = "TeamConnection"

    nodes: List[LinearTeam] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None


class TriageResponsibility(LinearModel):
    """Represents triage responsibility for a team."""
    linear_class_name: ClassVar[str] = "TriageResponsibility"

    id: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    archivedAt: Optional[datetime] = None
    action: Optional[str] = None
    team: Optional[LinearTeam] = None
    timeSchedule: Optional[Dict[str, Any]] = None
    currentUser: Optional[LinearUser] = None
