import depthai as dai
import robothub as rh

from app_pipeline import host_node
from node_helpers.timer import Timer

__all__ = ["VideoReporter"]


class VideoReporter(host_node.BaseNode):
    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self._buffer = rh.FrameBuffer(maxlen=rh.CONFIGURATION["fps"] * 120)
        self._last_video_event_sent = Timer()
        self._last_video_event_sent.reset()

    def __callback(self, message: dai.ImgFrame):
        img = message.getCvFrame()
        self._buffer.add_frame(packet=img)

    def trigger_video_report(self):
        if self._last_video_event_sent.has_elapsed(time_in_seconds=60 * 10):
            self._last_video_event_sent.reset()
            self._buffer.save_video_event(before_seconds=20, after_seconds=20, title="Video Report", fps=8,
                                          frame_width=rh.CONFIGURATION["merged_image_size"], frame_height=rh.CONFIGURATION["merged_image_size"],
                                          on_complete=self._send_video_event)

    def _send_video_event(self, video_path: str):
        rh.send_video_event(video=video_path, title="Video Report")
