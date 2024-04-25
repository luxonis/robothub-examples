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

# Get the root logger and change its log level and handlers
root_logger = log.getLogger()

# Clear existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Set new log level
root_logger.setLevel(log.DEBUG)

# Create a new handler with the desired format
new_handler = log.StreamHandler()
new_formatter = log.Formatter('%(levelname)s | %(funcName)s:%(lineno)s => %(message)s')
new_handler.setFormatter(new_formatter)

# Add the new handler to the root logger
root_logger.addHandler(new_handler)



class Application(rh.BaseDepthAIApplication):

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        device: dai.Device = self.get_device()
        create_pipeline(pipeline=pipeline, device=device)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        stereo_pairs: list[dai.StereoPair] = device.getStereoPairs()
        is_stereo_device = len(stereo_pairs) > 0
        log.info(f"Oak started, device has stereo: {is_stereo_device}. getting queues...")

        if not is_stereo_device:
            log.warning("Device has no stereo pairs, Depth stream will not be available.")

        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)
        detection_nn = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)
        detection_live_view = DepthaiLiveViewWrapper(name="detection_view", unique_key="rgb", width=1920, height=1080,
                                                     model_config_path="nn_models/detection_config.json")

        stereo_depth = None
        stereo_depth_frame: Optional[dai.ImgFrame] = None
        depth_live_view: Optional[DepthaiLiveViewWrapper] = None
        if is_stereo_device:
            stereo_depth = device.getOutputQueue(name="stereo_depth", maxSize=5, blocking=False)
            depth_live_view = DepthaiLiveViewWrapper(name="depth_view", unique_key="depth", width=1280, height=800,
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
