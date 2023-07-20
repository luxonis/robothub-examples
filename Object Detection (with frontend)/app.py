from threading import Event

import robothub_core
from depthai_sdk import OakCamera
from robothub_oak import LiveView, BaseApplication
from robothub_oak.data_processors import BaseDataProcessor
from robothub_oak.events import send_image_event


class ObjectDetection(BaseDataProcessor):
    def __init__(self, device_mxid: str):
        super().__init__()
        self.take_picture_signal = Event()
        self.device_mxid = device_mxid
        robothub_core.COMMUNICATOR.on_frontend(notification=self.on_fe_notification)

    def process_packets(self, packet):
        if self.take_picture_signal.is_set():
            self.take_picture_signal.clear()
            print("Sending Event!")
            send_image_event(packet.frame, 'Picture', self.device_mxid)

    def on_fe_notification(self, session_id, unique_key, payload):
        if unique_key == 'take_picture':
            print("Received take picture notification from FE")
            self.take_picture_signal.set()


class ExampleApplication(BaseApplication):
    def __init__(self):
        super().__init__()

    def setup_pipeline(self, device: OakCamera):
        """This method is the entrypoint for each device and is called upon connection."""
        color = device.create_camera(source="color", fps=30, resolution="1080p", encode="mjpeg")
        nn = device.create_nn(model='yolov6nr3_coco_640x352', input=color)

        LiveView.create(device=device, component=color, unique_key="nn_stream", name="Emotion recognition")

        object_detection = ObjectDetection(device.device.getMxId())
        device.callback(nn.out.main, object_detection)
