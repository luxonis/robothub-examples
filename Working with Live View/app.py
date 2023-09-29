from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from robothub import BaseApplication, LiveView


class LiveViewProcessor:
    def __init__(self, live_view):
        self.live_view = live_view

    def process_packets(self, packet: DetectionPacket):
        # LiveView implements several methods for drawing on the frame
        # Methods:
        #   - add_rectangle(rectangle: tuple, label: str), rectangle is required
        #   - add_line(p1: tuple, p2: tuple, color: tuple, thickness: int), p1 and p2 are required
        #   - add_text(text: str, coords: tuple), text and coords are required
        for detection in packet.detections:
            bbox = [*detection.top_left, *detection.bottom_right]
            self.live_view.add_rectangle(bbox, label=detection.label)

        # All coordinates must be denormalized (relative to the frame size)
        self.live_view.add_text(text='Hello, world!', coords=(10, 10))
        self.live_view.add_line(p1=(10, 10), p2=(10, 100))


class Application(BaseApplication):
    def setup_pipeline(self, oak: OakCamera):
        """This method is the entrypoint for the device and is called upon connection."""
        color = oak.create_camera(source='color', fps=30, encode='h264')
        nn = oak.create_nn('yolov5n_coco_416x416', input=color)

        live_view = LiveView.create(
            device=oak,
            component=color,
            name="Detection stream"
        )

        live_view_processor = LiveViewProcessor(live_view)
        oak.callback(nn.out.main, live_view_processor.process_packets)
