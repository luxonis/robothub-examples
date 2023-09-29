import time

from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from robothub import BaseApplication, LiveView
from robothub.events import send_image_event


class EventProcessor:
    def __init__(self, device_mxid):
        self.device_mxid = device_mxid
        self.last_upload = None

    def process_packets(self, packet: DetectionPacket):
        for detection in packet.detections:
            current_time = time.time()
            # 15 seconds cooldown
            if self.last_upload and current_time - self.last_upload < 15:
                return

            # Check if the person is located in the frame
            if detection.label == 'person':
                self.last_upload = current_time
                send_image_event(packet.frame, 'Person detected', self.device_mxid)


class Application(BaseApplication):
    def setup_pipeline(self, oak: OakCamera):
        """This method is the entrypoint for the device and is called upon connection."""
        color = oak.create_camera(source='color', fps=30, encode='mjpeg')
        nn = oak.create_nn('yolov5n_coco_416x416', input=color)

        LiveView.create(
            device=oak,
            component=color,
            name="Color stream"
        )

        event_processor = EventProcessor(oak.device.getMxId())
        oak.callback(nn.out.main, event_processor.process_packets)
