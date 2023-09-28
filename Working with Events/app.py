from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from robothub import BaseApplication, LiveView
from robothub.events import send_image_event


class EventProcessor:
    def __init__(self, device_mxid):
        self.device_mxid = device_mxid

    def process_packets(self, packet: DetectionPacket):
        for detection in packet.detections:
            bbox_center = detection.centroid()
            h, w = packet.frame.shape[:2]

            # Check if the person is located in the ROI - the right half of the frame
            if bbox_center[0] > w // 2 and detection.label == 'person':
                send_image_event(packet.frame, 'Person detected', self.device_mxid)


class ExampleApplication(BaseApplication):
    def setup_pipeline(self, oak: OakCamera):
        """This method is the entrypoint for the device and is called upon connection."""
        color = oak.create_camera(source='color', fps=30, encode='h264')
        nn = oak.create_nn('yolov5n_coco_416x416', input=color)

        LiveView.create(
            device=oak,
            component=color,
            name="Color stream"
        )

        event_processor = EventProcessor(oak.device.getMxId())
        oak.callback(nn.out.main, event_processor.process_packets)
