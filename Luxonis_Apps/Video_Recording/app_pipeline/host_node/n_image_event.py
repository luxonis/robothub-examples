import logging as log
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

    def __callback(self, message: Union[dai.ImgFrame, ControlMessage]) -> None:
        frame = message.getCvFrame()
        on_device_encoding = rh.CONFIGURATION["enable_jpeg_encoding_images"]
        log.info(f"About to send an image event with {on_device_encoding=}")
        rh.send_image_event(image=frame, title=f"Image event {datetime.now().strftime('%Y-%m-%d %H')}",
                            tags=["image_event"], encode=not on_device_encoding)
