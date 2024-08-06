import cv2

class PointTracker:
    def __init__(self):
        self.trackers = []
        self.boxes = []
        self.bbox_radius = 25
        self.frame = None
        self.tracking = True

    def toggle_tracking(self):
        self.tracking = not self.tracking

    def set_frame(self, frame):
        self.frame = frame

    def calculate_bbox_radius(self, point):
        # calculate ideal dynamic adaptive bbox for better tracking 
        return self.bbox_radius

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

        self.boxes = updated_boxes
        self.trackers = [tracker for tracker, bbox in zip(self.trackers, updated_boxes) if bbox is not None]

    def clear(self):
        self.trackers.clear()
        self.boxes.clear()
