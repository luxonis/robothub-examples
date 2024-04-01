
import depthai as dai
import logging as log
from base_node import BaseNode
from synchronisation import Synchronizer


class PeopleTrackingSync(BaseNode):

    def __init__(self):
        super().__init__()
        self._synchronizer = Synchronizer(number_of_messages_per_sequence_number=4)
        self._synchronizer.add_callback(self.__sync_callback)

    def __sync_callback(self, msgs: dict):
        self.send_message(message=msgs)

    def rgb_frame_callback(self, rgb_frame: dai.ImgFrame) -> None:
        self._synchronizer.add_message(message=rgb_frame, sequence_number=rgb_frame.getSequenceNum(), identifier="rgb")

    def rgb_mjpeg_frame_callback(self, rgb_mjpeg_frame: dai.ImgFrame) -> None:
        self._synchronizer.add_message(message=rgb_mjpeg_frame, sequence_number=rgb_mjpeg_frame.getSequenceNum(), identifier="rgb_mjpeg")

    def people_detections_callback(self, people_detections_frame: dai.ImgDetections) -> None:
        self._synchronizer.add_message(message=people_detections_frame, sequence_number=people_detections_frame.getSequenceNum(),
                                       identifier="people_detections")

    def object_tracker_callback(self, object_tracker_frame: dai.Tracklets) -> None:
        self._synchronizer.add_message(message=object_tracker_frame, sequence_number=object_tracker_frame.getSequenceNum(),
                                       identifier="object_tracker")
