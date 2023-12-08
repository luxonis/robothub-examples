
import depthai as dai
import logging as log

from base_node import BaseNode
from geometry import BoundingBox
from messages import PersonFiguresMessage, PersonFigure
from synchronisation import Synchronizer


class PeopleTracking(BaseNode):

    def __init__(self, input_node: BaseNode, re_id_queue: dai.DataOutputQueue):
        super().__init__()
        input_node.set_callback(self.tracking_callback)
        self.__re_id_queue = re_id_queue
        self.__re_id_memory = {}
        self.__lost_detections_memory = {}

    def tracking_callback(self, msgs: dict) -> None:
        rgb = msgs["rgb"]
        people_detections = msgs["people_detections"]
        object_tracker: dai.Tracklets = msgs["object_tracker"]
        person_figures = []
        for tracklet in object_tracker.tracklets:
            if tracklet.status == dai.Tracklet.TrackingStatus.NEW:
                log.debug(f"New tracklet: {tracklet.status}")
                re_id_vector = self.__get_re_id()
                self.__re_id_memory[tracklet.id] = re_id_vector
            elif tracklet.status == dai.Tracklet.TrackingStatus.LOST:
                if tracklet.id not in self.__lost_detections_memory:
                    self.__lost_detections_memory[tracklet.id] = 0
                self.__lost_detections_memory[tracklet.id] += 1
                # dont show lost detections more than 1 time
                if self.__lost_detections_memory[tracklet.id] > 2:
                    continue
            elif tracklet.status == dai.Tracklet.TrackingStatus.TRACKED:
                self.__lost_detections_memory[tracklet.id] = 0

            elif tracklet.status == dai.Tracklet.TrackingStatus.REMOVED:
                r = self.__re_id_memory.pop(tracklet.id, None)
                log.debug(f"Tracklet {tracklet.id} removed: re_id is None: {r is None}")
                continue
            # construct a message
            xmin = tracklet.roi.topLeft().x
            ymin = tracklet.roi.topLeft().y
            xmax = tracklet.roi.bottomRight().x
            ymax = tracklet.roi.bottomRight().y
            person_box = BoundingBox(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, image_width=1920, image_height=1080,
                                     confidence=tracklet.srcImgDetection.confidence)
            person_figure = PersonFigure(re_id=self.__re_id_memory.get(tracklet.id, -1), bbox=person_box, tracking_id=tracklet.id)
            person_figures.append(person_figure)
        message = PersonFiguresMessage(person_figures=person_figures, rgb_image=rgb, sequence_number=object_tracker.getSequenceNum())
        self.send_message(message=message)

    def __get_re_id(self):
        if self.__re_id_queue is None:
            return []
        re_id_message = self.__re_id_queue.get()
        re_id_vector = re_id_message.getFirstLayerFp16()
        return re_id_vector

