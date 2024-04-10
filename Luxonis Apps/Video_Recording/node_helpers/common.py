
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True, kw_only=True)
class Timestamp:
    utc: datetime
    local: datetime

    def __init__(self):
        self.utc: datetime = datetime.now(timezone.utc)
        self.local: datetime = datetime.now(timezone.utc).astimezone()

    def __sub__(self, other: "Timestamp") -> float:
        """Return the difference in seconds between two timestamps."""
        return (self.utc - other.utc).total_seconds()


@dataclass(slots=True, frozen=True, kw_only=True)
class TimestampedData:
    timestamps: list[Timestamp]
    data: list[Any]
