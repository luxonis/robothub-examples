import robothub as rh
import depthai as dai


class OverlayHandler:
    def __init__(self, detection_view: rh.DepthaiLiveView, labels: list[str]):
        self.detection_view = detection_view
        self.labels = labels

    def add_rectangle_overlays_on_detections(self, detections: dai.ImgDetections):
        for detection in detections.detections:
            bbox = detection.xmin, detection.ymin, detection.xmax, detection.ymax
            self.detection_view.add_rectangle(bbox, label=self.labels[detection.label])
