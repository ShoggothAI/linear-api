"""
Linear API Client Library.

A well-organized client for interacting with the Linear API.
"""

from .client import LinearClient

from .domain import (
    # Common models
    LinearIssue,
    LinearProject,
    LinearUser,
    LinearTeam,
    LinearState,
    LinearLabel,
    LinearAttachment,
    # Input models
    LinearIssueInput,
    LinearIssueUpdateInput,
    LinearAttachmentInput,
    # Enums
    LinearPriority,
    IntegrationService,
    SLADayCountType,
    ProjectStatusType,
)

__version__ = "0.2.0"
__all__ = [
    # Main client
    "LinearClient",
    # Common models
    "LinearIssue",
    "LinearProject",
    "LinearUser",
    "LinearTeam",
    "LinearState",
    "LinearLabel",
    "LinearAttachment",
    # Input models
    "LinearIssueInput",
    "LinearIssueUpdateInput",
    "LinearAttachmentInput",
    # Enums
    "LinearPriority",
    "IntegrationService",
    "SLADayCountType",
    "ProjectStatusType",
]
