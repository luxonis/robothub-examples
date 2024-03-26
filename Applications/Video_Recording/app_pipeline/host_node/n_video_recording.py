import logging as log
from collections import deque

import depthai as dai
import robothub as rh
from app_pipeline import host_node
from app_pipeline.messages import VideoBufferMessage
from node_helpers import common


class VideoRecording(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        maxlen = rh.CONFIGURATION["fps"] * 60 * 5  # 5 min max
        log.info(f"Max On Demand Video length: {maxlen}")
        self._buffer = deque(maxlen=maxlen)
        self._timestamp_buffer = deque(maxlen=maxlen)

        self._recording = False
        self._send_data = False

    def __callback(self, h264_frame: dai.ImgFrame) -> None:
        if self._recording:
            self._buffer.append(h264_frame)
            self._timestamp_buffer.append(common.Timestamp())

        if self._send_data:
            self._send_data = False
            buffer = common.TimestampedData(timestamps=list(self._timestamp_buffer), data=list(self._buffer))
            message = VideoBufferMessage(sequence_number=h264_frame.getSequenceNum(), buffer=buffer)
            self.send_message(message=message)

    def switch_on(self) -> None:
        if self._recording:
            return
        self._recording = True

    def switch_off(self) -> None:
        if self._recording:
            self._recording = False
            self._send_data = True
        return



