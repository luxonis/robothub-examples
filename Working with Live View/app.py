from depthai_sdk import OakCamera
from depthai_sdk.classes import DetectionPacket
from robothub import BaseApplication, LiveView


class BusinessLogic:
    live_view = None

    def process_packets(self, packet: DetectionPacket):
        # LiveView implements several methods for drawing on the frame
        # Methods:
        #   - add_rectangle(rectangle: tuple, label: str), rectangle is required
        #   - add_line(pt1: tuple, pt2: tuple, color: tuple, thickness: int), p1 and p2 are required
        #   - add_text(text: str, coords: tuple), text and coords are required
        for detection in packet.detections:
            bbox = [*detection.top_left, *detection.bottom_right]
            self.live_view.add_rectangle(bbox, label=detection.label)

        # All coordinates must be denormalized (relative to the frame size)
        self.live_view.add_text(text='Hello, world!', coords=(50, 50))
        self.live_view.add_line(pt1=(100, 100), pt2=(100, 200))


class Application(BaseApplication):
    business_logic = BusinessLogic()

    def setup_pipeline(self, oak: OakCamera):
        """
        Define your data pipeline. Can be called multiple times during runtime. Make sure that objects that have to be created only once
        are defined either as static class variables or in the __init__ method of this class.
        """
        color = oak.create_camera(source='color', fps=30, encode='h264')
        nn = oak.create_nn('yolov5n_coco_416x416', input=color)
        self.business_logic.live_view = LiveView.create(device=oak, component=color, name="Detection stream", manual_publish=False)
        # define where you want to process data from the camera
        oak.callback(nn.out.main, self.live_view_processor.process_packets)
