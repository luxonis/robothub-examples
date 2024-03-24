import robothub as rh
import depthai as dai
from handlers import OverlayHandler
from utils import get_labels


class DepthaiLiveViewWrapper:
    def __init__(self, name: str, unique_key: str, width: int, height: int, model_config_path: str):
        self._depthai_live_view = rh.DepthaiLiveView(name=name, unique_key=unique_key, width=width, height=height)
        self._overlay_handler = OverlayHandler(detection_view=self._depthai_live_view,
                                               labels=get_labels(model_config_path))

    def update(self, frame: dai.ImgFrame, detections: dai.ImgDetections = None):
        if detections:
            self._overlay_handler.add_rectangle_overlays_on_detections(detections=detections)
        self._depthai_live_view.publish(frame.getFrame())
