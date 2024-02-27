import time

import depthai
import depthai as dai
from pathlib import Path

import logging as log
import robothub as rh
from robothub.events import send_image_event

from pipeline import create_pipeline


class Application(rh.BaseDepthAIApplication):

    def __init__(self):
        # App
        super().__init__()

    def setup_pipeline(self) -> dai.Pipeline:
        pipeline = dai.Pipeline()
        create_pipeline(pipeline=pipeline, config=self.config)
        return pipeline

    def manage_device(self, device: depthai.Device):
        log.info(f"DepthAi version: {dai.__version__}")
        log.info(f"Oak started. getting queues...")
        rgb_preview = device.getOutputQueue(name="rgb_preview", maxSize=5, blocking=False)
        rgb_mjpeg = device.getOutputQueue(name="rgb_mjpeg", maxSize=5, blocking=False)
        detection_nn = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)

        node = self.pipeline.getNode(0)
        print(node)

        live_view = rh.LiveView.create(component=self.pipeline.getNode(), name="Color stream")
        while self.running:
            rgb_frame: dai.ImgFrame = rgb_preview.get()
            rgb_mjpeg_frame: dai.ImgFrame = rgb_mjpeg.get()
            detections: dai.ImgDetections = detection_nn.get()
            for detection in detections.detections:
                if detection.label == 0:
                    frame_size = rgb_frame.getWidth(), rgb_frame.getHeight()
                    bbox = int(detection.xmin * frame_size[0]), int(detection.ymin * frame_size[1]), int(
                        detection.xmax * frame_size[0]), int(detection.ymax * frame_size[1])
                    live_view.add_rectangle(bbox, label=self.config["mappings"]["labels"][0])
                    rh.events.send_image_event(image=rgb_mjpeg_frame.getFrame(), title="Person detected", device_id=device.getMxId())
            time.sleep(0.01)

if __name__ == '__main__':
    app = Application()
    app.run()