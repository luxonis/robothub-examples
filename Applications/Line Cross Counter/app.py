import depthai as dai
import numpy as np

from depthai_sdk import OakCamera
from numpy import linalg as LA
from robothub import LiveView
from robothub.application import BaseApplication


class LineCrossingCounter:
    # Define line using absolute coordinates, illustrated below as *'s.
    # -----------
    # |    *    |
    # |    *    |
    # |    *    |
    # |    *    |
    # -----------
    LINE_P1 = [1920 // 2, 0]
    LINE_P2 = [1920 // 2, 1080]

    # Counters
    left_to_right = 0
    right_to_left = 0

    # Buffer for the algorithm
    previous_positions: dict = {}

    live_view: LiveView = None

    def process_packets(self, packets):
        color_packet = packets['color']
        nn_packet = packets['3_out;0_video']

        tracklets = nn_packet.daiTracklets.tracklets
        detections = nn_packet.detections

        # Iterate through all tracklets
        for detection, tracklet in zip(detections, tracklets):
            tracklet_id = tracklet.id
            tracklet_status = tracklet.status

            # If tracklet is lost, remove it from the buffer
            if tracklet_status == dai.Tracklet.TrackingStatus.LOST:
                self.previous_positions.pop(tracklet_id, None)
                continue

            bbox = [*detection.top_left, *detection.bottom_right]
            # Get current and previous position of the tracklet
            h, w = nn_packet.frame.shape[:2]
            normalized_roi = tracklet.roi.denormalize(w, h)
            current_position = self.get_roi_center(normalized_roi)
            previous_position = self.previous_positions.get(tracklet_id, None)

            # Check if previous position exists, if not, we are in the first frame
            if previous_position is not None:
                points = [self.LINE_P1, self.LINE_P2, previous_position, current_position]
                if self.intersect(*points):  # Check if trail intersects with the line
                    angle = self.calc_vector_angle(*points)  # Calculate angle between the trail and the line

                    if angle < 180:  # If angle is less than 180 degrees, the person is moving from left to right
                        self.left_to_right += 1
                    else:  # Otherwise, the person is moving from right to left
                        self.right_to_left += 1

            self.previous_positions[tracklet_id] = current_position
            self.live_view.add_rectangle(rectangle=bbox, label=detection.label)

        # Visualizations
        self.live_view.add_text(f"Left to right: {self.left_to_right}, Right to left: {self.right_to_left}",
                                coords=(100, 100))
        self.live_view.add_line(self.LINE_P1, self.LINE_P2)
        self.live_view.publish(color_packet.frame)

    def calc_vector_angle(self, point1, point2, point3, point4):
        """Calculate the angle between two vectors formed by four points."""
        u = self.create_vector(point1, point2)
        v = self.create_vector(point3, point4)
        return self.angle_between_vectors(u, v)

    @staticmethod
    def create_vector(point1, point2):
        """Create a vector from two points."""
        return np.array([point2[0] - point1[0], point2[1] - point1[1]])

    @staticmethod
    def angle_between_vectors(u, v):
        """Calculate angle between two vectors."""
        i = np.inner(u, v)
        n = LA.norm(u) * LA.norm(v)
        c = i / n
        a = np.rad2deg(np.arccos(np.clip(c, -1.0, 1.0)))
        return a if np.cross(u, v) < 0 else 360 - a

    def intersect(self, A, B, C, D):
        """Return true if line segments AB and CD intersect."""
        return self.ccw(A, C, D) != self.ccw(B, C, D) and self.ccw(A, B, C) != self.ccw(A, B, D)

    @staticmethod
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    @staticmethod
    def get_roi_center(roi):
        """Calculate ROI center."""
        return np.array([roi.x + roi.width / 2, roi.y + roi.height / 2])


class Application(BaseApplication):
    line_cross_counter = LineCrossingCounter()

    def setup_pipeline(self, oak: OakCamera):
        """
        Define your data pipeline. Can be called multiple times during runtime. Make sure that objects that have to be created only once
        are defined either as static class variables or in the __init__ method of this class.
        """
        color = oak.create_camera(source='color', fps=15, encode='h264')
        detection_nn = oak.create_nn(model='yolov6n_coco_640x640', input=color, tracker=True)
        detection_nn.config_nn(resize_mode='stretch')
        detection_nn.config_tracker(tracker_type=dai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM,
                                    track_labels=[0],  # track people only
                                    assignment_policy=dai.TrackerIdAssignmentPolicy.UNIQUE_ID,
                                    forget_after_n_frames=5)

        self.line_cross_counter.live_view = LiveView.create(device=oak, component=color, name='Line Cross stream', unique_key=f'line_cross_stream',
                                                            manual_publish=True)
        oak.sync([color.out.encoded, detection_nn.out.tracker], self.line_cross_counter.process_packets)
