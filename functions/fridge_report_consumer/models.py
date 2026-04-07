"""Data models (TypedDicts) shared across the User Rewards service modules."""

from __future__ import annotations

from typing import TypedDict

class StatusReport(TypedDict):
    fridgeId: str
    epochTimestamp: int
    condition: str
    foodPercentage: int


class AwardResult(TypedDict):
    """Return type of get_award()."""

    points: int
    action_count_name: str


# Model
class UserPointsHistoryItem(TypedDict):
    """Item shape for UserPointsHistory."""
    awardId: str
    newReport: TypedDict
    userId: str
    actionTypes: list[str]
    points: int
    occurredAt: int
    createdAt: str


# Model
class UserActionStatsItem(TypedDict):
    """Item shape for UserActionStats"""

    userId: str
    totalPoints: int
    fridgeReportCount: int
    cleanedCount: int
    filledCount: int
    repairedCount: int
    lastUpdated: str
