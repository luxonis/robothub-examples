import cv2
import numpy as np

class PointTracker:
    bbox_increase_step = 5
    bbox_radius = 20 
    max_bbox_radius = 200

    def __init__(self):
        self.trackers = []
        self.boxes = []
        self.frame = None
        self.tracking = True

    def toggle_tracking(self):
        self.tracking = not self.tracking

    def set_frame(self, frame):
        self.frame = frame

    def calculate_bbox_radius(self, point):
        bbox_radius = self.bbox_radius # start with default value

        while True:
            bbox = (
                max(0, int(point[0] - bbox_radius)),
                max(0, int(point[1] - bbox_radius)),
                min(self.frame.shape[1], int(bbox_radius*2)),
                min(self.frame.shape[0], int(bbox_radius*2))
            )

            roi = self.frame[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]]

            edge_density = self.get_edge_density(roi)

            if edge_density > 0.1 or bbox_radius >= self.max_bbox_radius:
                break

            bbox_radius += self.bbox_increase_step

        return bbox_radius

    def get_edge_density(self, roi):
        edges = cv2.Canny(roi, 100, 200) 
        edge_density = np.sum(edges) / (roi.shape[0] * roi.shape[1])
        return edge_density

    def add_point(self, point):
        if len(self.boxes) == 2:
            self.clear()
        bbox_radius = self.calculate_bbox_radius(point)
        bbox = (point[0] - bbox_radius, point[1] - bbox_radius, bbox_radius*2, bbox_radius*2)

        tracker = cv2.TrackerCSRT.create()
        tracker.init(self.frame, bbox)

        self.trackers.append(tracker)
        self.boxes.append(bbox)

    def update(self):
        if len(self.boxes) == 0 or not self.tracking:
            return None, None

        updated_boxes = []
        for tracker in self.trackers:
            success, bbox = tracker.update(self.frame)
            if success:
                updated_boxes.append(bbox)
            else:
                updated_boxes.append(None)

        self.boxes = [bbox for bbox in updated_boxes if bbox is not None]
        self.trackers = [tracker for tracker, bbox in zip(self.trackers, updated_boxes) if bbox is not None]

    def clear(self):
        self.trackers.clear()
        self.boxes.clear()
