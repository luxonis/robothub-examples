import time

from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from robothub import BaseApplication, LiveView
from robothub.events import send_image_event
from robothub_core import CONFIGURATION


class EventProcessor:
    def __init__(self):
        self.device_mxid = None
        self.last_upload = None

    def process_packets(self, packet: DetectionPacket):
        for detection in packet.detections:
            current_time = time.time()
            # 15 seconds cooldown
            if self.last_upload and current_time - self.last_upload < CONFIGURATION["event_upload_interval"]:
                return
            # Check if the person is located in the frame
            if detection.label == 'person':
                self.last_upload = current_time
                send_image_event(image=packet.frame, title='Person detected', device_id=self.device_mxid)


class Application(BaseApplication):
    event_processor = EventProcessor()

    def setup_pipeline(self, oak: OakCamera):
        """
        Define your data pipeline. Can be called multiple times during runtime. Make sure that objects that have to be created only once
        are defined either as static class variables or in the __init__ method of this class.
        """
        color = oak.create_camera(source='color', fps=30, encode='mjpeg')
        nn = oak.create_nn('yolov5n_coco_416x416', input=color)
        LiveView.create(device=oak, component=color, name="Color stream")
        self.event_processor.device_mxid = oak.device.getMxId()
        oak.callback(nn.out.main, self.event_processor.process_packets)
