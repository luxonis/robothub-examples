import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

class PointTracker:
    bbox_increase_step = 5
    bbox_padding_step = 13 # what is added at the end of the bbox
    bbox_radius = 10 
    max_bbox_radius = 200
    similarity_threshold = 0.3 # the higher the value, the more similar the images need to be
    debounce_threshold = 2
    motion_threshold = 0.5
    modes = {
        1: {'name': 'tracking', 'tracking': 2},
        2: {'name': 'meter', 'tracking': 1},
        3: {'name': 'static', 'tracking': 0}
    }

    def __init__(self):
        self.points = []
        self.frame = None
        self.prev_frame = None
        self.mode = self.modes[1] 

    def set_mode(self, mode):
        if mode == 2: self.clear()
        self.mode = self.modes[mode]

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

        # Subsample the images by taking every nth pixel (subsampling factor)
        subsample_factor = 10
        prev_gray_subsampled = prev_gray[::subsample_factor, ::subsample_factor]
        curr_gray_subsampled = curr_gray[::subsample_factor, ::subsample_factor]

        # Calculate optical flow on the subsampled images
        flow = cv2.calcOpticalFlowFarneback(prev_gray_subsampled, curr_gray_subsampled, None, 
                                            pyr_scale=0.5, levels=1, winsize=13, iterations=2, 
                                            poly_n=5, poly_sigma=1.1, flags=0)

        # Compute motion magnitude
        motion_magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        mean_motion = np.mean(motion_magnitude)
        # print(mean_motion)

        return mean_motion

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

        return bbox_radius + self.bbox_padding_step

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

        if self.mode['tracking'] == 1:
            tracker = cv2.TrackerCSRT.create()
            tracker.init(self.frame, bbox)

            self.points.append({
                'bbox': bbox,
                'tracker': tracker,
                'roi': self.frame[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]],
            })


    def _debounce(self, old_bbox, new_bbox):
       return all(abs(old_bbox[i] - new_bbox[i]) < self.debounce_threshold for i in range(4))

    def _is_bbox_out_of_frame(self, bbox):
        return (bbox[0] < 0 or bbox[1] < 0 or 
            bbox[0] + bbox[2] > self.frame.shape[1] or 
            bbox[1] + bbox[3] > self.frame.shape[0])

    def update(self):
        if len(self.points) == 0:
            return

        # enumerate to know indices of points as well 
        for i, data in enumerate(self.points):
            tracker = data['tracker']
            old_bbox = data['bbox']
            prev_roi = data['roi']

            if self.mode['tracking'] == 2 or (self.mode['tracking'] == 1 and i == 1):
                success, new_bbox = tracker.update(self.frame)
                if success and not self._is_bbox_out_of_frame(new_bbox):
                    if self._debounce(old_bbox, new_bbox) and self.calculate_global_motion() < self.motion_threshold:
                        new_bbox = old_bbox  # keep the old bounding box

                    data['bbox'] = new_bbox
                    old_bbox = new_bbox

            new_roi = self.frame[old_bbox[1]:old_bbox[1]+old_bbox[3], old_bbox[0]:old_bbox[0]+old_bbox[2]]

            if new_roi.shape[0] == 0 or new_roi.shape[1] == 0:
                continue

            data['roi'] = new_roi 

            # update bbox if roi has changed
            if self.roi_changed(prev_roi, new_roi):
                center_x = int(old_bbox[0] + old_bbox[2] // 2)
                center_y = int(old_bbox[1] + old_bbox[3] // 2)

                new_radius = self.calculate_bbox_radius((center_x, center_y))
                new_bbox = (center_x - new_radius, center_y - new_radius, new_radius*2, new_radius*2)
                tracker.init(self.frame, new_bbox)
                data['bbox'] = new_bbox

    def clear(self):
        self.points.clear()
