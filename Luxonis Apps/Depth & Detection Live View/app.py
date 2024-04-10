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
from wrappers import DepthaiLiveViewWrapper


class Application(rh.BaseDepthAIApplication):

    def __init__(self):
        super().__init__()
        self.detection_live_view = DepthaiLiveViewWrapper(name="detection_view", unique_key="rgb", width=1920, height=1080,
                                                          model_config_path="nn_models/detection_config.json")
        self.depth_live_view = DepthaiLiveViewWrapper(name="depth_view", unique_key="depth", width=1280, height=800,
                                                      model_config_path="nn_models/detection_config.json")

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline)
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

            self.detection_live_view.update(frame=rgb_h264_frame, detections=detections)
            self.depth_live_view.update(frame=stereo_depth_frame)
            time.sleep(0.01)


if __name__ == "__main__":
    app = Application()
    app._run()
