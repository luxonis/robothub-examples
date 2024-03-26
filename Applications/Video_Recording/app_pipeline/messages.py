import logging as log
from dataclasses import dataclass

import depthai as dai
import robothub as rh
from node_helpers.common import TimestampedData


@dataclass(slots=True, kw_only=True)
class Message:
    sequence_number: int

    def getSequenceNum(self) -> int:
        return self.sequence_number


@dataclass(slots=True, kw_only=True)
class VideoBufferMessage(Message):
    buffer: TimestampedData
