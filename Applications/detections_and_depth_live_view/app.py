import time

# cv2 and av bug workaround
import cv2
import numpy as np

cv2.imshow("bugfix", np.zeros((10, 10, 3), dtype=np.uint8))
cv2.destroyWindow("bugfix")

import depthai as dai

import logging as log
import robothub as rh

from pipeline import create_pipeline
from utils import get_labels
from handlers import OverlayHandler


class Application(rh.BaseDepthAIApplication):

    def __init__(self):
        super().__init__()
        self.detection_view = rh.DepthaiLiveView(name="detection_view", unique_key="rgb", width=1920, height=1080)
        self.depth_view = rh.DepthaiLiveView(name="depth_view", unique_key="depth", width=1920, height=1080)
        self.overlay_handler = OverlayHandler(detection_view=self.detection_view,
                                              labels=get_labels(model_config_path="nn_models/detection_config.json"))

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline, config=rh.CONFIGURATION)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)
        stereo_depth = device.getOutputQueue(name="stereo_depth", maxSize=5, blocking=False)
        detection_nn = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)

        while rh.app_is_running:
            rgb_h264_frame: dai.ImgFrame = rgb_h264.get()
            stereo_depth_frame: dai.ImgFrame = stereo_depth.get()
            detections: dai.ImgDetections = detection_nn.get()

            self.overlay_handler.add_rectangle_overlays_on_detections(detections=detections)

            self.detection_view.publish(h264_frame=rgb_h264_frame.getFrame())
            self.depth_view.publish(h264_frame=stereo_depth_frame.getFrame())
            time.sleep(0.01)


if rh.LOCAL_DEV:
    app = Application()
    app.run()
