import time

from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from robothub import BaseApplication, LiveView
from robothub.events import send_image_event
from robothub_core import CONFIGURATION


class BusinessLogic:
    def __init__(self):
        self.last_image_event_upload_seconds = time.time()
        self.last_video_event_upload_seconds = time.time()
        self.live_view = None

    def process_packets(self, packet: DetectionPacket):
        for detection in packet.detections:
            # visualize bounding box in the live view
            bbox = [*detection.top_left, *detection.bottom_right]
            self.live_view.add_rectangle(bbox, label=detection.label)

            current_time_seconds = time.time()
            # arbitrary condition for sending image events to RobotHub
            if current_time_seconds - self.last_image_event_upload_seconds > CONFIGURATION["image_event_upload_interval_minutes"] * 60:
                if detection.label == 'person':
                    self.last_image_event_upload_seconds = current_time_seconds
                    send_image_event(image=packet.frame, title='Person detected')
            # arbitrary condition for sending video events to RobotHub
            if current_time_seconds - self.last_video_event_upload_seconds > CONFIGURATION["video_event_upload_interval_minutes"] * 60:
                if detection.label == 'person':
                    self.last_video_event_upload_seconds = current_time_seconds
                    self.live_view.save_video_event(before_seconds=60, after_seconds=60, title="Interesting video")


class Application(BaseApplication):
    business_logic = BusinessLogic()

    def setup_pipeline(self, oak: OakCamera):
        """Define the pipeline using depthai-sdk."""

        color = oak.create_camera(source='color', resolution="1080p", fps=30, encode='mjpeg')
        nn = oak.create_nn(model='yolov5n_coco_416x416', input=color)
        self.business_logic.live_view = LiveView.create(
            device=oak,
            component=color,
            name="Color stream",
            max_buffer_size=120
        )
        oak.callback(output=nn.out.main, callback=self.business_logic.process_packets)