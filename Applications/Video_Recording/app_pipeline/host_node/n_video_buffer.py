import logging as log
from collections import deque

import depthai as dai
import robothub as rh
from app_pipeline import host_node
from app_pipeline.messages import VideoBufferMessage
from node_helpers import common


class VideoBuffer(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        maxlen = rh.CONFIGURATION["fps"] * 60 * 5  # 5 min max
        log.info(f"Video Buffer length: {maxlen}")
        self._buffer = deque(maxlen=maxlen)
        self._timestamp_buffer = deque(maxlen=maxlen)

    def __callback(self, h264_frame: dai.ImgFrame) -> None:
        self._buffer.append(h264_frame)
        self._timestamp_buffer.append(common.Timestamp())

    def send_video(self) -> VideoBufferMessage:
        buffer = common.TimestampedData(timestamps=list(self._timestamp_buffer), data=list(self._buffer))
        message = VideoBufferMessage(sequence_number=buffer.data[-1].getSequenceNum(), buffer=buffer)
        self.send_message(message=message)
