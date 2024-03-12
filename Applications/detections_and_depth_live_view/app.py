import json
import time
from pathlib import Path

# cv2 and av bug workaround
import cv2
import numpy as np

cv2.imshow("bugfix", np.zeros((10, 10, 3), dtype=np.uint8))
cv2.destroyWindow("bugfix")

import depthai as dai

import logging as log
import robothub as rh

from pipeline import create_pipeline


class Application(rh.BaseDepthAIApplication):

    def __init__(self):
        super().__init__()
        self.detection_view = rh.DepthaiLiveView(name="detection_view", unique_key="rgb", width=1920, height=1080)
        self.depth_view = rh.DepthaiLiveView(name="depth_view", unique_key="depth", width=1920, height=1080)

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline, config=self.config)
        return pipeline

    def manage_device(self, device: dai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_h264 = device.getOutputQueue(name="rgb_h264", maxSize=5, blocking=False)
        stereo_depth = device.getOutputQueue(name="stereo_depth", maxSize=5, blocking=False)
        detection_nn = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)

        model_config = Path("nn_models/detection_config.json")
        with model_config.open() as f:
            config = json.loads(f.read())

        while self.running:
            rgb_h264_frame: dai.ImgFrame = rgb_h264.get()
            stereo_depth_frame: dai.ImgFrame = stereo_depth.get()
            detections: dai.ImgDetections = detection_nn.get()
            for detection in detections.detections:
                if detection.label == 0:
                    frame_size = self.detection_view.frame_width, self.detection_view.frame_height
                    bbox = int(detection.xmin * frame_size[0]), int(detection.ymin * frame_size[1]), int(
                        detection.xmax * frame_size[0]), int(detection.ymax * frame_size[1])
                    self.detection_view.add_rectangle(bbox, label=config["mappings"]["labels"][0])
            self.detection_view.publish(h264_frame=rgb_h264_frame.getFrame())
            self.depth_view.publish(h264_frame=stereo_depth_frame.getFrame())
            time.sleep(0.01)


if __name__ == '__main__':
    if rh.LOCAL_DEV:
        app = Application()
        app.run()
