"""
Team-related domain models for Linear API.

This module defines models related to teams in the Linear API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, ClassVar, List

from pydantic import Field

from .base_domain import LinearModel


class LinearState(LinearModel):
    """
    Represents a workflow state in Linear.
    """
    linear_class_name: ClassVar[str] = "WorkflowState"

    id: str
    name: str
    type: str
    color: str


class LinearTeam(LinearModel):
    """
    Represents a team in Linear.
    """
    linear_class_name: ClassVar[str] = "Team"

    id: str
    name: str
    key: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class TeamConnection(LinearModel):
    """
    Connection model for teams.
    """
    linear_class_name: ClassVar[str] = "TeamConnection"

    nodes: List[LinearTeam] = Field(default_factory=list)
    pageInfo: Optional[Dict[str, Any]] = None
