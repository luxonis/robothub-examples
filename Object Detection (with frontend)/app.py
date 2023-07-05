from threading import Event

import robothub
from robothub_oak import DEVICE_MANAGER


class ObjectDetection(robothub.RobotHubApplication):
    def on_start(self):
        # Get first connected device
        device = DEVICE_MANAGER.get_all_devices()[0]

        # Create a YoloV6 object detection NN with color sensor as input 
        color = device.get_camera('color', resolution='1080p', fps=30)
        nn = device.create_neural_network('yolov6nr3_coco_640x352', color)

        # Create a video stream
        nn.stream_to_hub(name=f'Object Detection Stream', unique_key='nn_stream')
        # Set a callback to the NN output
        nn.add_callback(self.stream_frame_callback)

        # Set callback to handle notification messages coming from the frontend
        robothub.COMMUNICATOR.on_frontend(notification=self.on_fe_notification)
        self.take_picture_signal = Event()

    def on_fe_notification(self, session_id, unique_key, payload):
        if unique_key == 'take_picture':
            print("Received take picture notification from FE")
            self.take_picture_signal.set()

    def stream_frame_callback(self, frame):
        if self.take_picture_signal.is_set():
            self.take_picture_signal.clear()
            print("Sending Event!")
            frame.upload_as_detection(title='Object Detections')

    def start_execution(self):
        DEVICE_MANAGER.start()

    def on_stop(self):
        DEVICE_MANAGER.stop()
