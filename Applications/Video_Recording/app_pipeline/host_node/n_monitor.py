import depthai as dai
import robothub as rh
from app_pipeline import host_node
from node_helpers import decorators
from node_helpers.alerts import TimeEvent


class Monitor(host_node.BaseNode):
    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self._get_width_height()
        self.main_live_view = rh.DepthaiLiveView(name="color_stream", unique_key="color_stream",
                                                 width=rh.CONFIGURATION["image_width"], height=rh.CONFIGURATION["image_height"])
        self._recording_on = False
        self._recording_duration = TimeEvent.zero()

    @decorators.measure_call_frequency
    def __callback(self, message: dai.ImgFrame):
        rec_duration = self._recording_duration.seconds_elapsed()
        text = f"Rec: {'ON' if self._recording_on else 'OFF'}, Rec. duration: {rec_duration:.1f} seconds"
        size = 4 if rh.CONFIGURATION["resolution"] == "4k" else 2
        self.main_live_view.add_text(text=text, coords=(80, 80), background_color=(0, 0, 0), background_transparency=0.8, size=size)
        self.main_live_view.publish(h264_frame=message.getCvFrame())

    @staticmethod
    def _get_width_height():
        width_mapping = {"4k": 3840, "1080p": 1920, "720p": 1280}
        height_mapping = {"4k": 2160, "1080p": 1080, "720p": 720}
        rh.CONFIGURATION["image_width"] = width_mapping[rh.CONFIGURATION["resolution"]]
        rh.CONFIGURATION["image_height"] = height_mapping[rh.CONFIGURATION["resolution"]]

    def toggle_recording_on(self):
        self._recording_on = True
        self._recording_duration = TimeEvent()

    def toggle_recording_off(self):
        self._recording_on = False
        self._recording_duration = TimeEvent.zero()
