import logging as log
import time

import cv2
import depthai as dai

import config

from depthai_sdk import OakCamera, FramePacket
from depthai_sdk.components import CameraComponent

from circle.circle_manager import CircleManager
from helpers import init_logger
from overlay.overlay_display_standalone import OverlayDisplayerStandalone
from overlay.overlay_manager import OverlayManager

init_logger()


class CupsApp:
    # circle_manager = CircleManager()
    oak: OakCamera = None
    running: bool = True
    circle_manager: CircleManager = CircleManager(OverlayManager(OverlayDisplayerStandalone()))

    def run(self):
        self.connect()
        self.setup_pipeline()
        self.start_pipeline()

    def connect(self):
        self.oak = OakCamera()

    def setup_pipeline(self):
        color_camera = self.oak.create_camera(source='color', resolution='1080p', fps=config.FPS, encode='mjpeg')
        self.init_control_queue(color_camera)
        # cv2.namedWindow("Circles", cv2.WINDOW_NORMAL)
        self.oak.callback(color_camera.out.encoded, self.find_and_show_circles, main_thread=True)

    def start_pipeline(self):
        self.oak.start(blocking=False)
        # get dai queues
        thermal_out: dai.DataOutputQueue = self.oak.device.getOutputQueue(name="thermal", maxSize=5, blocking=False)
        while self.running:
            time.sleep(0.001)
            self.poll()
            # poll depthai queues
            thermal_packet: dai.ADa = thermal_out.tryGet()
            if thermal_packet is not None:
                self.process_thermal(thermal_packet)

    def poll(self):
        try:
            self.oak.poll()
        except Exception as e:
            log.error(f"Polling failed: {e}")
            log.info(f"Terminating program...")
            self.oak.__exit__(1, 2, 3)
            self.oak = None
            self.running = False

    def find_and_show_circles(self, rgb_packet: FramePacket):
        encoded_frame = rgb_packet.msg.getCvFrame()
        image_frame = cv2.imdecode(encoded_frame, cv2.IMREAD_COLOR)
        self.circle_manager.refresh_circles(image_frame)
        cv2.imshow("Circles", image_frame)
        # cv2.waitKey(1)

    def process_thermal(self, thermal_packet: FramePacket):
        pass

    def init_control_queue(self, color_camera: CameraComponent):
        cam_control = self.oak.pipeline.createXLinkIn()
        cam_control.setMaxDataSize(1)
        cam_control.setNumFrames(1)
        cam_control.setStreamName('control')
        cam_control.out.link(color_camera.node.inputControl)

    def set_auto_exposure_roi(self, oak_camera: OakCamera):
        cam_control_queue = oak_camera.device.getInputQueue('control')

        x, y, width, height = (
            tuple(map(int, config.AUTO_EXPOSURE_ROI.split(',')))
            if len(config.AUTO_EXPOSURE_ROI.strip()) > 0
            else (0, 0, 1, 1)
        )

        message = dai.CameraControl()
        message.setAutoExposureRegion(startX=x, startY=y, width=width, height=height)
        message.setAutoExposureEnable()

        cam_control_queue.send(message)

        log.info(f"AE set to {x = }, {y = }, {width = }, {height = }")


if __name__ == '__main__':
    cups_app = CupsApp()
    cups_app.run()
