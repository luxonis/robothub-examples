import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

class PointTracker:
    bbox_increase_step = 5
    bbox_radius = 20 
    max_bbox_radius = 200
    similarity_threshold = 0.4 # the higher the value, the more similar the images need to be
    debounce_threshold = 5
    motion_threshold = 0.8

    def __init__(self):
        self.points = []
        self.frame = None
        self.prev_frame = None
        self.tracking = True

    def toggle_tracking(self):
        self.tracking = not self.tracking

    def set_frame(self, frame):
        self.prev_frame = self.frame
        self.frame = frame

    def get_boxes(self):
        return [point['bbox'] for point in self.points] 

    def get_points(self):
        return [(bbox[0] + bbox[2] // 2, bbox[1] + bbox[3] // 2) for bbox in self.get_boxes()]

    # this calculates the global motion of the frame 
    # more info: https://docs.opencv.org/3.4/dc/d6b/group__video__track.html#ga5d10ebbd59fe09c5f650289ec0ece5af
    def calculate_global_motion(self):
        if self.prev_frame is None:
            return

        prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)

        motion_magnetude = np.sqrt(flow[...,0]**2 + flow[...,1]**2)
        mean = np.mean(motion_magnetude)
        # print(mean)
        return mean

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

    def roi_changed(self, prev_roi, new_roi):
        prev_roi_gray = cv2.cvtColor(prev_roi, cv2.COLOR_BGR2GRAY) if len(prev_roi.shape) == 3 else prev_roi
        new_roi_gray = cv2.cvtColor(new_roi, cv2.COLOR_BGR2GRAY) if len(new_roi.shape) == 3 else new_roi

        # Resize the new_roi to match prev_roi size
        if prev_roi_gray.shape != new_roi_gray.shape:
            new_roi_gray = cv2.resize(new_roi_gray, (prev_roi_gray.shape[1], prev_roi_gray.shape[0]))

        score, _ = ssim(prev_roi_gray, new_roi_gray, full=True)
        return score < self.similarity_threshold

    def add_point(self, point):
        if len(self.points) == 2:
            self.clear()
        bbox_radius = self.calculate_bbox_radius(point)
        bbox = (point[0] - bbox_radius, point[1] - bbox_radius, bbox_radius*2, bbox_radius*2)

        tracker = cv2.TrackerCSRT.create()
        tracker.init(self.frame, bbox)

        self.points.append({
            'bbox': bbox,
            'tracker': tracker,
            'roi': self.frame[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]],
        })

    def update(self):
        if len(self.points) == 0 or not self.tracking:
            return

        for data in self.points:
            tracker = data['tracker']
            old_bbox = data['bbox']
            prev_roi = data['roi']

            success, new_bbox = tracker.update(self.frame)
            if success:
                if new_bbox[0] < 0 or new_bbox[1] < 0 or new_bbox[0] + new_bbox[2] > self.frame.shape[1] or new_bbox[1] + new_bbox[3] > self.frame.shape[0]:
                    continue
                # debounce 
                if abs(old_bbox[0] - new_bbox[0]) < self.debounce_threshold and \
                   abs(old_bbox[1] - new_bbox[1]) < self.debounce_threshold and \
                   abs(old_bbox[2] - new_bbox[2]) < self.debounce_threshold and \
                   abs(old_bbox[3] - new_bbox[3]) < self.debounce_threshold and \
                    self.calculate_global_motion() < self.motion_threshold: 
                    print("debounce - keep the old bbox")
                    new_bbox = old_bbox  # Keep the old bounding box
                else:
                    print("new bbox")

                center_x = int(new_bbox[0] + new_bbox[2] // 2)
                center_y = int(new_bbox[1] + new_bbox[3] // 2)

                new_roi = self.frame[new_bbox[1]:new_bbox[1]+new_bbox[3], new_bbox[0]:new_bbox[0]+new_bbox[2]]

                if new_roi.shape[0] == 0 or new_roi.shape[1] == 0:
                    continue

                if self.roi_changed(prev_roi, new_roi):
                    new_radius = self.calculate_bbox_radius((center_x, center_y))
                    new_bbox = (center_x - new_radius, center_y - new_radius, new_radius*2, new_radius*2)
                    tracker.init(self.frame, new_bbox)

                data['bbox'] = new_bbox
                data['roi'] = new_roi 

    def clear(self):
        self.points.clear()
