import logging as log
from collections import deque

import depthai as dai
import robothub as rh
from app_pipeline import host_node
from app_pipeline.controlls import Control
from app_pipeline.messages import ControlMessage, VideoBufferMessage
from node_helpers import common


class VideoBuffer(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode, buffer_size_minutes: int = 5):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self.maxlen = rh.CONFIGURATION["fps"] * 60 * buffer_size_minutes
        log.info(f"Video Buffer length: {self.maxlen}")
        self._buffer = deque(maxlen=self.maxlen)
        self._timestamp_buffer = deque(maxlen=self.maxlen)
        self._clear_buffers = False

    def __callback(self, message: ControlMessage) -> None:
        h264_frame: dai.ImgFrame = message.message
        if message.control == Control.TURN_ON:
            self.add_to_buffer(h264_frame)
        elif message.control == Control.TURN_OFF:
            self.add_to_buffer(h264_frame)
            buffer = common.TimestampedData(timestamps=list(self._timestamp_buffer), data=list(self._buffer))
            message = VideoBufferMessage(sequence_number=buffer.data[-1].getSequenceNum(), buffer=buffer)
            self.send_message(message=message)
        if self._clear_buffers:
            self.__clear_buffers()

    def add_to_buffer(self, h264_frame: dai.ImgFrame) -> None:
        self._buffer.append(h264_frame)
        self._timestamp_buffer.append(common.Timestamp())

    def clear_buffers(self) -> None:
        self._clear_buffers = True

    def __clear_buffers(self):
        self._buffer.clear()
        self._timestamp_buffer.clear()
        self._clear_buffers = False
