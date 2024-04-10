import logging as log
from dataclasses import dataclass
from typing import Optional, Union

import depthai as dai
import robothub as rh
from node_helpers.common import TimestampedData
from app_pipeline.controlls import Control


@dataclass(slots=True, kw_only=True)
class Message:
    sequence_number: int

    def getSequenceNum(self) -> int:
        return self.sequence_number


@dataclass(slots=True, kw_only=True)
class ControlMessage:
    message: Union[Message, dai.ImgFrame]
    control: Control

    def getSequenceNum(self) -> int:
        return self.message.getSequenceNum()

    def getCvFrame(self):
        try:
            return self.message.getCvFrame()
        except AttributeError:
            log.error(f"No cv frame in message {self.message}")
            return None


@dataclass(slots=True, kw_only=True)
class VideoBufferMessage(Message):
    buffer: TimestampedData
