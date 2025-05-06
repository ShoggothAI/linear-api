"""
Enumeration types for Linear API.

This module defines all enum types used across the Linear API.
"""

from enum import Enum, StrEnum


class LinearPriority(Enum):
    """Enum for issue priority levels"""
    URGENT = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    NONE = 4


class SLADayCountType(StrEnum):
    """Enum for SLA day count types"""
    ALL = "all"
    ONLY_BUSINESS_DAYS = "onlyBusinessDays"


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


class Day(StrEnum):
    """Enum for days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


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
