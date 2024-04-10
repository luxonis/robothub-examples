from datetime import datetime
from typing import Optional, Union

import depthai as dai
import robothub as rh
from app_pipeline import host_node
from app_pipeline.messages import ControlMessage


class ImageEvent(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self._last_frame: Optional[dai.ImgFrame] = None

    def __callback(self, message: Union[dai.ImgFrame, ControlMessage]) -> None:
        self._last_frame = message.getCvFrame()
        self.send_image()

    def send_image(self) -> None:
        rh.send_image_event(image=self._last_frame, title=f"Image event {datetime.now().strftime('%Y-%m-%d %H')}",
                            tags=["image_event"])
