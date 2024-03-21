import time
import logging as log

### cv2 and av bug workaround - uncomment in local dev

# import cv2
# import numpy as np
#
# cv2.imshow("bugfix", np.zeros((10, 10, 3), dtype=np.uint8))
# cv2.destroyWindow("bugfix")

import depthai as dai
import robothub as rh

from pipeline import create_pipeline
from handlers import EventHandler


class Application(rh.BaseDepthAIApplication):

    def __init__(self):
        super().__init__()
        self.detection_view = rh.DepthaiLiveView(name="detection_view", unique_key="rgb", width=1920, height=1080)
        self.event_handler = EventHandler()

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline, config=rh.CONFIGURATION)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)
        rgb_mjpeg = device.getOutputQueue(name="rgb_mjpeg", maxSize=5, blocking=False)
        detection_nn = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)

        while rh.app_is_running:
            rgb_h264_frame: dai.ImgFrame = rgb_h264.get()
            rgb_mjpeg_frame: dai.ImgFrame = rgb_mjpeg.get()
            detections: dai.ImgDetections = detection_nn.get()

            self.event_handler.send_image_event_on_detection_if_interval_elapsed(detections=detections,
                                                                                 rgb_mjpeg_frame=rgb_mjpeg_frame,
                                                                                 device_id=device.getMxId())

            self.event_handler.send_image_event_on_fe_notification(rgb_mjpeg_frame=rgb_mjpeg_frame,
                                                                   device_id=device.getMxId())

            self.detection_view.publish(h264_frame=rgb_h264_frame.getFrame())
            time.sleep(0.01)


if rh.LOCAL_DEV:
    app = Application()
    app.run()
