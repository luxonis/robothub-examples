import logging as log
import cv2 as cv
import depthai as dai
from depthai_sdk import OakCamera, FramePacket
from depthai_sdk.components import CameraComponent
from robothub import BaseApplication, LiveView

from circle.circle_manager import CircleManager
from helpers import init_logger
from overlay.overlay_display_robothub import OverlayDisplayerRobothub
from overlay.overlay_manager import OverlayManager

init_logger()


class Application(BaseApplication):
    overlay_displayer = OverlayDisplayerRobothub()
    circle_manager = CircleManager(OverlayManager(overlay_displayer))

    def setup_pipeline(self, oak: OakCamera):
        color_camera = oak.create_camera(source='color', resolution='1080p', fps=self.config['fps'], encode='mjpeg')
        self.init_control_queue(oak, color_camera)

        live_view = LiveView.create(device=oak, component=color_camera, name='Stream')
        self.overlay_displayer.set_live_view(live_view)

        oak.callback(color_camera.out.main, self.video_callback)

    def on_device_connected(self, oak: OakCamera) -> None:
        self.set_auto_exposure_roi(oak)

    def video_callback(self, packet: FramePacket):
        image_frame = cv.imdecode(packet.msg.getCvFrame(), cv.IMREAD_COLOR)
        self.circle_manager.refresh_circles(image_frame)

    def init_control_queue(self, oak_camera: OakCamera, color_camera: CameraComponent):
        cam_control = oak_camera.pipeline.createXLinkIn()
        cam_control.setMaxDataSize(1)
        cam_control.setNumFrames(1)
        cam_control.setStreamName('control')
        cam_control.out.link(color_camera.node.inputControl)

    def set_auto_exposure_roi(self, oak_camera: OakCamera):
        cam_control_queue = oak_camera.device.getInputQueue('control')

        x, y, width, height = (
            tuple(map(int, self.config['auto_exposure_roi'].split(',')))
            if len(self.config['auto_exposure_roi'].strip()) > 0
            else (0, 0, 1, 1)
        )

        message = dai.CameraControl()
        message.setAutoExposureRegion(startX=x, startY=y, width=width, height=height)
        message.setAutoExposureEnable()

        cam_control_queue.send(message)

        log.info(f"AE set to {x = }, {y = }, {width = }, {height = }")
