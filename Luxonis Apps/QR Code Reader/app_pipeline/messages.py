from dataclasses import dataclass

import depthai as dai
import numpy as np
from datetime import datetime
import cv2
import base64

from node_helpers import BoundingBox

__all__ = ["Message", "FramesWithDetections", "QrBoundingBoxes", "RhReport", "HighResFrame"]


@dataclass(slots=True, kw_only=True)
class Message:
    sequence_number: int

    def getSequenceNum(self) -> int:
        return self.sequence_number


@dataclass(slots=True, kw_only=True)
class QrBoundingBoxes(Message):
    bounding_boxes: list[BoundingBox]


@dataclass(slots=True, kw_only=True)
class HighResFrame(Message):
    frame: np.ndarray


@dataclass(slots=True, kw_only=True)
class FramesWithDetections(Message):
    high_res_rgb: HighResFrame
    h264_frame: dai.ImgFrame
    qr_bboxes: QrBoundingBoxes


@dataclass(slots=True, kw_only=True)
class RhReport(Message):
    context_image: np.ndarray
    qr_bboxes: QrBoundingBoxes


@dataclass(slots=True, kw_only=True)
class WebReport(Message):
    crop_image: np.ndarray
    label: str
    code_format: str
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "code_format": self.code_format,
            "timestamp": str(self.timestamp),
            "crop_image": self.__encode_image_to_base64()
        }

    def __encode_image_to_base64(self) -> str:
        """Convert np.ndarray to string."""
        _, buffer = cv2.imencode('.jpg', self.crop_image)
        encoded_string = base64.b64encode(buffer).decode('utf-8')
        return encoded_string
