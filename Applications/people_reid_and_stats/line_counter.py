import decorators as deco
import depthai as dai
import logging as log
import numpy as np
import time

from base_node import BaseNode
from line_manager import LineManager
from messages import PersonFiguresMessage
from numpy import linalg as LA
from settings import IMAGE_WIDTH, IMAGE_HEIGHT


class LineCounter(BaseNode):
    def __init__(self, source_node: BaseNode):
        super().__init__()
        source_node.set_callback(self.__process_packets)
        self.line_manager = LineManager()
        # SDK
        self.cam_width = IMAGE_WIDTH
        self.cam_height = IMAGE_HEIGHT

        self.previous_positions: dict = {}

    @deco.measure_average_performance
    @deco.measure_call_frequency
    def __process_packets(self, msgs: dict) -> None:
        color_packet = msgs['rgb']
        nn_packet: dai.ImgDetections = msgs['people_detections']
        object_tracker: dai.Tracklets = msgs['object_tracker']

        tracklets = object_tracker.tracklets
        detections = nn_packet.detections

        for detection, tracklet in zip(detections, tracklets):
            tracklet_id = tracklet.id
            tracklet_status = tracklet.status

            if tracklet_status == dai.Tracklet.TrackingStatus.LOST or tracklet_status == dai.Tracklet.TrackingStatus.REMOVED:
                self.previous_positions[tracklet_id] = None
                continue

            h, w = 1080, 1920
            normalized_roi = tracklet.roi.denormalize(w, h)
            current_position = self.get_roi_center(normalized_roi)
            previous_position = self.previous_positions.get(tracklet_id, None)

            # Check if previous position exists, if not, we are in the first frame
            if previous_position is not None:
                line_entities = self.line_manager.line_entities

                for line in line_entities:
                    if line["isDisabled"]:
                        continue
                    if line["trackLabelId"] != "all" and labelMap[detection.label] not in line["detectionLabels"]:
                        continue
                    x1 = line["x1"] * self.cam_width
                    y1 = line["y1"] * self.cam_height
                    x2 = line["x2"] * self.cam_width
                    y2 = line["y2"] * self.cam_height
                    line_point_1 = [x1, y1]
                    line_point_2 = [x2, y2]
                    points = [line_point_1, line_point_2, previous_position, current_position]
                    if self.intersect(*points):
                        line["count"] += 1
                        line["lastCrossAt"] = time.time()

            self.previous_positions[tracklet_id] = current_position

    def get_roi_center(self, roi):
        """Calculate ROI center."""
        return np.array([roi.x + roi.width / 2, roi.y + roi.height / 2])

    def ccw(self, A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    def intersect(self, A, B, C, D):
        """Return true if line segments AB and CD intersect."""
        return self.ccw(A, C, D) != self.ccw(B, C, D) and self.ccw(A, B, C) != self.ccw(A, B, D)

    def create_vector(self, point1, point2):
        """Create a vector from two points."""
        return np.array([point2[0] - point1[0], point2[1] - point1[1]])

    def angle_between_vectors(self, u, v):
        """Calculate angle between two vectors."""
        i = np.inner(u, v)
        n = LA.norm(u) * LA.norm(v)
        c = i / n
        a = np.rad2deg(np.arccos(np.clip(c, -1.0, 1.0)))
        return a if np.cross(u, v) < 0 else 360 - a

    def calc_vector_angle(self, point1, point2, point3, point4):
        """Calculate the angle between two vectors formed by four points."""
        u = self.create_vector(point1, point2)
        v = self.create_vector(point3, point4)
        return self.angle_between_vectors(u, v)

labelMap = [
    "person",
    "bicycle",
    "car",
    "motorbike",
    "aeroplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "sofa",
    "pottedplant",
    "bed",
    "diningtable",
    "toilet",
    "tvmonitor",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush"
]

