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
    sequence_number: int


@dataclass
class Person:
    figure: PersonFigure
    face_features: Optional[FaceFeature]

@dataclass
class PeopleFacesMessage:
    people: list[Person]
    image: dai.ImgFrame
