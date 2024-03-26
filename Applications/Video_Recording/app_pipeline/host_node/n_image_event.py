from datetime import datetime
from typing import Optional

import depthai as dai
import robothub as rh
from app_pipeline import host_node


class ImageEvent(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self._last_frame: Optional[dai.ImgFrame] = None

    def __callback(self, frame_mjpeg: dai.ImgFrame) -> None:
        self._last_frame = frame_mjpeg

    def send_image(self) -> None:
        rh.send_image_event(image=self._last_frame.getCvFrame(), title=f"Image event {datetime.now().strftime('%Y-%m-%d %H')}",
                            tags=["image_event"])
