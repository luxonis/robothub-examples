import logging as log
from typing import Optional

### cv2 and av bug workaround on some linux systems - uncomment in local dev

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

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        device: dai.Device = self.get_device()
        create_pipeline(pipeline=pipeline, device=device)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")

        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)
        detection_nn = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)
        detection_live_view = DepthaiLiveViewWrapper(name="detection_view", unique_key="rgb", width=1920, height=1080,
                                                     model_config_path="nn_models/detection_config.json")

        

        while rh.app_is_running and self.device_is_running:
            try:
                rgb_h264_frame: dai.ImgFrame = rgb_h264.get()
                detections: dai.ImgDetections = detection_nn.get()
                if stereo_depth is not None:
                    stereo_depth_frame = stereo_depth.get()
            except RuntimeError:
                log.error(f"Connection to the device was lost, restarting device...")
                self.restart_device()

            detection_live_view.update(frame=rgb_h264_frame, detections=detections)
            if depth_live_view is not None and stereo_depth_frame is not None:
                depth_live_view.update(frame=stereo_depth_frame)


if __name__ == "__main__":
    app = Application()
    app.run()
