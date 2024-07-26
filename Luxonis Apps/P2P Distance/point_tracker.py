import cv2

class PointTracker:
    def __init__(self):
        self.tracker1 = cv2.legacy.TrackerCSRT_create()
        self.tracker2 = cv2.legacy.TrackerCSRT_create()
        self.points = []

    def add_point(self, frame, point):
        if len(self.points) == 2:
            self.clear()
        bbox = (point[0] - 10, point[1] - 10, 20, 20)
        if len(self.points) == 1:
            self.tracker2 = cv2.legacy.TrackerCSRT_create()
            self.tracker2.init(frame, bbox)
        else:
            self.tracker1 = cv2.legacy.TrackerCSRT_create()
            self.tracker1.init(frame, bbox)
        self.points.append(point)

    def update(self, frame):
        if len(self.points) == 0:
            return None, None
        success1, bbox1 = self.tracker1.update(frame)
        success2, bbox2 = self.tracker2.update(frame)
        if success1 and success2:
            p1 = (int(bbox1[0] + bbox1[2] / 2), int(bbox1[1] + bbox1[3] / 2))
            p2 = (int(bbox2[0] + bbox2[2] / 2), int(bbox2[1] + bbox2[3] / 2))
            self.points = [p1, p2]
            return p1, p2
        return None, None

    def clear(self):
        self.points.clear()
        self.tracker1.clear()
        self.tracker2.clear()
