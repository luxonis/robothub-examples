import logging as log

import depthai as dai
import robothub as rh
import zxingcpp
import cv2

from app_pipeline import host_node, messages

__all__ = ["QrCodeDecoder"]


class QrCodeDecoder(host_node.BaseNode):
    """Add cr code text to qr bounding boxes."""
    DECODE_CHANNEL = 0  # blue channel should be enough for QR decoding
    PADDING = 20

    def __init__(self, input_node: host_node.BaseNode, qr_crop_queue: dai.DataOutputQueue):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self._qr_crop_queue = qr_crop_queue

    @rh.decorators.measure_average_performance(report_every_minutes=0.3)
    def __callback(self, frames_and_detections: messages.FramesWithDetections):
        qr_bboxes = frames_and_detections.qr_bboxes
        expected_crops = len(qr_bboxes.bounding_boxes)
        i = 0
        for bbox in qr_bboxes.bounding_boxes:
            log.debug(f"Getting crop {i} of {expected_crops}")
            i += 1
            crop = self._qr_crop_queue.get()
            bbox.set_crop(crop=crop)
            cv2.imshow(f"crop{i}", bbox.crop.getCvFrame())

        qr_bboxes.bounding_boxes = host_node.ReconstructQrDetections.perform_nms_on_bboxes(bounding_boxes=qr_bboxes.bounding_boxes)

        for bbox in qr_bboxes.bounding_boxes:
            crop_frame = bbox.crop.getCvFrame()
            crop_frame = crop_frame[:, :, self.DECODE_CHANNEL]
            width, height = crop_frame.shape
            if width > 0 and height > 0:
                decoded_codes = zxingcpp.read_barcodes(crop_frame)
                if len(decoded_codes) > 0:
                    decoded_code = decoded_codes[0]
                    bbox.set_label(label=decoded_code.text)
        # cv2.imshow("4k", high_res_frame)
        self.send_message(frames_and_detections)
