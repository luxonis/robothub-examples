import depthai as dai
import numpy as np

from dataclasses import dataclass
from geometry import BoundingBox
from typing import Optional


@dataclass
class FaceFeature:
    bbox: BoundingBox
    age: int
    gender: str
    emotion: str

    def __hash__(self):
        # Use the hash of the immutable content for the object hash
        return hash(self.bbox.absolute)

    def __eq__(self, other):
        # Two FaceFeature objects are equal if their features are equal
        return (self.bbox.absolute[0] == other.bbox.absolute[0] and self.bbox.absolute[1] == other.bbox.absolute[1]
                and self.bbox.absolute[2] == other.bbox.absolute[2] and self.bbox.absolute[3] == other.bbox.absolute[3])


@dataclass
class FaceData:
    sequence_number: int
    data: list[FaceFeature]


@dataclass
class PeopleTrackingMessage:
    sequence_number: int
    tracklets: dai.Tracklets
    image: dai.ImgFrame


@dataclass
class PersonFigure:
    re_id: np.ndarray
    tracking_id: int
    bbox: BoundingBox


@dataclass
class PersonFiguresMessage:
    person_figures: list[PersonFigure]
    rgb_image: dai.ImgFrame
    rgb_mjpeg_image: dai.ImgFrame
    sequence_number: int


@dataclass
class Person:
    figure: PersonFigure
    face_features: Optional[FaceFeature]

@dataclass
class PeopleFacesMessage:
    people: list[Person]
    image: dai.ImgFrame
    image_mjpeg: dai.ImgFrame
