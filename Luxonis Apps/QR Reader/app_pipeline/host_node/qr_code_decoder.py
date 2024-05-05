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

            crop = self._qr_crop_queue.get()
            log.debug(f"App: {i}, {bbox.frame_sequence_number=} {crop.getSequenceNum()=}")
            i += 1
            bbox.set_crop(crop=crop)

        qr_bboxes.bounding_boxes = host_node.ReconstructQrDetections.perform_nms_on_bboxes(bounding_boxes=qr_bboxes.bounding_boxes)
        for bbox in qr_bboxes.bounding_boxes:
            crop_frame = bbox.crop.getCvFrame()
            crop_frame = crop_frame[:, :, self.DECODE_CHANNEL]
            width, height = crop_frame.shape
            if rh.LOCAL_DEV:
                cv2.imshow(f"crop{bbox.counter}", crop_frame)
            if width > 0 and height > 0:
                try:
                    decoded_codes = zxingcpp.read_barcodes(crop_frame)
                except IndexError:
                    continue
                if len(decoded_codes) > 0:
                    if len(decoded_codes) > 1:
                        log.warning(f"More than one QR code detected in crop {i}")
                    decoded_code = decoded_codes[0]
                    bbox.set_label(label=decoded_code.text)
        # cv2.imshow("4k", high_res_frame)
        if len(qr_bboxes.bounding_boxes) > 0:
            if qr_bboxes.bounding_boxes[0].crop.getSequenceNum()!= qr_bboxes.bounding_boxes[-1].crop.getSequenceNum():
                # this should never happen, would mean error in pipeline setup, probably some queue is not blocking and messages get lost
                log.critical(
                    f"Sequence numbers are not the same: {qr_bboxes.bounding_boxes[0].crop.getSequenceNum()} != {qr_bboxes.bounding_boxes[-1].crop.getSequenceNum()}")
                # FindStart.reset()
                # self._crop_count = 0
        self.send_message(frames_and_detections)
