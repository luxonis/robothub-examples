import depthai
import numpy as np
import robothub
from numpy import linalg as LA
from robothub_oak.manager import DEVICE_MANAGER
from robothub_oak.packets import TrackerPacket

import depthai_sdk


class LineCrossApplication(robothub.RobotHubApplication):
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

    def on_start(self):
        """
        This method is called when the application is started.
        We use it to create a neural network and stream its output to the RobotHub.
        """

        devices = DEVICE_MANAGER.get_all_devices()  # Get all assigned devices
        for device in devices:
            # Define color camera and person detection model
            color = device.get_camera('color', resolution='1080p', fps=15)
            nn = device.create_neural_network('yolov6n_coco_640x640', color, tracker=True)

            # Configure tracker
            nn.configure_tracker(tracker_type=depthai.TrackerType.ZERO_TERM_COLOR_HISTOGRAM,
                                 track_labels=[1],  # track people only
                                 assignment_policy=depthai.TrackerIdAssignmentPolicy.SMALLEST_ID)

            # Define a stream to send the NN output to the RobotHub with a custom callback
            nn.stream_to_hub(
                name=f'NN stream {device.id}',  # Name of the stream (shown in Live View)
                output_type='tracker',
                visualizer_callback=self.on_detection  # Callback function to be called when a new packet is received
            )

    def on_stop(self):
        """
        This method is called when the application is stopped. Use it as destructor.
        """
        DEVICE_MANAGER.stop()

    def start_execution(self):
        """
        This method is called after on_start() and is used to start the execution of the application.
        """
        DEVICE_MANAGER.start()

    def on_detection(self, packet: TrackerPacket):
        # Get tracklets and visualizer from the packet
        tracklets = packet.tracklets
        visualizer = packet.visualizer

        # Iterate through all tracklets
        for tracklet in tracklets:
            tracklet_id = tracklet.id

            # Get current and previous position of the tracklet
            h, w = visualizer.frame_shape
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

        # Add text and line to be shown in Live View 
        visualizer.add_text(f"Left to right: {self.left_to_right}, Right to left: {self.right_to_left}",
                            background_color=(0, 0, 0),
                            position=depthai_sdk.TextPosition.TOP_MID)
        visualizer.add_line(self.LINE_P1, self.LINE_P2)
        visualizer.detections(hide_label=True)

    # Helper functions

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
