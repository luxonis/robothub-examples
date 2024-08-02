import cv2

class PointTracker:
    def __init__(self):
        self.trackers = []
        self.points = []
        self.bbox_radius = 25
        self.frame = None
        self.tracking = True

    def toggle_tracking(self):
        self.tracking = not self.tracking

    def set_frame(self, frame):
        self.frame = frame

    def add_point(self, point):
        if len(self.points) == 2:
            self.clear()
        bbox = (point[0] - self.bbox_radius, point[1] - self.bbox_radius, self.bbox_radius*2, self.bbox_radius*2)
        tracker = cv2.legacy.TrackerCSRT_create()
        tracker.init(self.frame, bbox)
        self.trackers.append(tracker)
        self.points.append(point)

    def update(self):
        if len(self.points) == 0 or not self.tracking:
            return None, None

        updated_points = []
        for i in range(len(self.points)):
            success, bbox = self.trackers[i].update(self.frame)
            if success:
                updated_point = (int(bbox[0] + bbox[2] / 2), int(bbox[1] + bbox[3] / 2))
                updated_points.append(updated_point)
            else:
                updated_points.append(None)

        self.points = [p for p in updated_points if p is not None]
        self.trackers = [self.trackers[i] for i in range(len(self.trackers)) if updated_points[i] is not None]

        if len(self.points) == 2:
            return self.points[0], self.points[1]
        elif len(self.points) == 1:
            return self.points[0], None
        return None, None

    def clear(self):
        self.points.clear()
        self.trackers.clear()
