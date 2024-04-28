import cv2
import robothub as rh

from app_pipeline import host_node
from app_pipeline.messages import FramesWithDetections

__all__ = ["Monitor"]


class Monitor(host_node.BaseNode):
    def __init__(self, input_node: host_node.BaseNode, name: str):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self.name = name
        self._live_view = rh.DepthaiLiveView(name="Preview Live View", unique_key=rh.DEVICE_MXID, width=1280, height=720,
                                             device_mxid=rh.DEVICE_MXID)

    def __callback(self, message: FramesWithDetections):
        img = message.rgb_preview.getCvFrame()
        bboxes = message.qr_bboxes.bounding_boxes
        for bbox in bboxes:
            label = f"{bbox.label}, {bbox.confidence:.3f}"
            # draw bounding box
            cv2.rectangle(img, (bbox.xmin, bbox.ymin), (bbox.xmax, bbox.ymax), color=(255, 255, 255))
            # draw label
            cv2.putText(img, label, (bbox.xmin, bbox.ymin - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow(self.name, img)
        cv2.waitKey(1)
