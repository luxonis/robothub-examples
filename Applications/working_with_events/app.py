import time
from threading import Event

import depthai as dai

import logging as log
import robothub as rh

from pipeline import create_pipeline


class Application(rh.BaseDepthAIApplication):

    def __init__(self):
        super().__init__()
        self.detection_view = rh.DepthaiLiveView(name="detection_view", unique_key="rgb", width=1920, height=1080)
        self.last_upload = None
        self.take_picture_signal = Event()
        rh.COMMUNICATOR.on_frontend(notification=self.on_fe_notification)

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline, config=self.config)
        return pipeline

    def on_fe_notification(self, session_id, unique_key, payload):
        if unique_key == 'take_picture':
            print("Received take picture notification from FE")
            self.take_picture_signal.set()

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)
        rgb_mjpeg = device.getOutputQueue(name="rgb_mjpeg", maxSize=5, blocking=False)
        detection_nn = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)

        while self.running:
            rgb_h264_frame: dai.ImgFrame = rgb_h264.get()
            rgb_mjpeg_frame: dai.ImgFrame = rgb_mjpeg.get()
            detections: dai.ImgDetections = detection_nn.get()
            for detection in detections.detections:
                current_time = time.time()
                if self.last_upload and current_time - self.last_upload < self.config["event_upload_interval"]:
                    continue
                if detection.label == 0:
                    self.last_upload = current_time
                    rh.events.send_image_event(image=rgb_mjpeg_frame.getFrame(), title="Person detected",
                                               device_id=device.getMxId())
            if self.take_picture_signal.is_set():
                self.take_picture_signal.clear()
                log.info(f"Sending Event...")
                rh.events.send_image_event(image=rgb_mjpeg_frame.getFrame(), title="Front-end event image",
                                           device_id=device.getMxId())
            self.detection_view.publish(h264_frame=rgb_h264_frame.getFrame())
            time.sleep(0.01)


if __name__ == '__main__':
    if rh.LOCAL_DEV:
        app = Application()
        app.run()
