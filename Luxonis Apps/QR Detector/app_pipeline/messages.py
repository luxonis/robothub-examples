from dataclasses import dataclass

import depthai as dai
import numpy as np

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
class FramesWithDetections(Message):
    high_res_rgb: np.ndarray
    qr_bboxes: QrBoundingBoxes


@dataclass(slots=True, kw_only=True)
class HighResFrame(Message):
    frame: np.ndarray


@dataclass(slots=True, kw_only=True)
class RhReport(Message):
    context_image: np.ndarray
    qr_bboxes: QrBoundingBoxes
