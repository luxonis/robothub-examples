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
        img = message.rgb_h264.getCvFrame()
        bboxes = message.qr_bboxes.bounding_boxes
        for bbox in bboxes:
            label = f"{bbox.label}, {bbox.confidence:.3f}"
            self._live_view.add_rectangle(rectangle=(bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax), label=label)

        self._live_view.publish(h264_frame=img)
