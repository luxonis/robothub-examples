import time

import depthai
import depthai as dai
from pathlib import Path

import logging as log
from robothub import LiveView
from robothub.application import BaseDepthAIApplication
from robothub.robothub_core_wrapper import CONFIGURATION

from pipeline import create_pipeline


class Application(BaseDepthAIApplication):

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
        rgb_mjpeg = device.getOutputQueue(name="rgb_mjpeg", maxSize=5, blocking=False)
        detections = device.getOutputQueue(name="detection_nn", maxSize=5, blocking=False)

        # TODO figure out image annotation and how to send the image

