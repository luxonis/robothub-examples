import logging as log

import cv2
import depthai as dai
import robothub as rh

from app_pipeline import host_node, messages, script_node
from node_helpers import BoundingBox, FindStart

__all__ = ["ReconstructQrDetections"]


class ReconstructQrDetections(host_node.BaseNode):
    """
    From 9 detection messages, reconstruct 1 message with all 9 detections.
    Apply NMS and recalculate bboxes from the crop space to frame space.
    """

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)
        self._TOTAL_CROP_COUNT = script_node.NUMBER_OF_CROPPED_IMAGES
        self._find_start = FindStart(sequence_length=self._TOTAL_CROP_COUNT)
        self._find_start.disable()
        self._sequence_number = 0
        self._crop_count = 0
        self._x_offset = 0
        self._y_offset = 0
        self._bounding_boxes: list[BoundingBox] = []

        self._CROP_WIDTH = rh.CONFIGURATION["high_res_crop_width"]
        self._CROP_HEIGHT = rh.CONFIGURATION["high_res_crop_height"]
        self._FRAME_WIDTH = rh.CONFIGURATION["merged_image_width"]
        self._FRAME_HEIGHT = rh.CONFIGURATION["merged_image_height"]
        # not overlap but crop size - overlap
        self._OVERLAP_WIDTH = 450 if rh.CONFIGURATION["resolution"] == "5312x6000" else 768 - 192
        self._OVERLAP_HEIGHT = 450 if rh.CONFIGURATION["resolution"] == "5312x6000" else 432 - 108

    def __callback(self, yolo_output: dai.ImgDetections):
        log.debug(f"Got detections for sequence number {yolo_output.getSequenceNum()}")
        # if not self._find_start(yolo_output):
        #     return
        self._sequence_number = yolo_output.getSequenceNum()
        self._transform_to_frame_space(detections=yolo_output)
        self._send_results()
        self._increase_crop_count()
        self._update_coord_offset()

    def _transform_to_frame_space(self, detections: dai.ImgDetections) -> None:
        log.debug(f"{self._crop_count=} xoff: {self._x_offset} yoff: {self._y_offset}")
        new_bboxes = []
        for detection in detections.detections:
            detection: dai.ImgDetection
            xmin_abs_crop = int(detection.xmin * self._CROP_WIDTH)
            ymin_abs_crop = int(detection.ymin * self._CROP_HEIGHT)
            xmax_abs_crop = int(detection.xmax * self._CROP_WIDTH)
            ymax_abs_crop = int(detection.ymax * self._CROP_HEIGHT)

            xmin_abs_frame = xmin_abs_crop + self._x_offset
            ymin_abs_frame = ymin_abs_crop + self._y_offset
            xmax_abs_frame = xmax_abs_crop + self._x_offset
            ymax_abs_frame = ymax_abs_crop + self._y_offset
            log.debug(f"CropNR: seq_num {detections.getSequenceNum()} nr: {self._crop_count}")

            log.debug(f"CropNR: {self._crop_count}\n"
                      f"Det: xmin: {detection.xmin} ymin: {detection.ymin} xmax: {detection.xmax} ymax: {detection.ymax},\n"
                      f"Old: xmin: {xmin_abs_crop} ymin: {ymin_abs_crop} xmax: {xmax_abs_crop} ymax: {ymax_abs_crop},\n"
                      f"New: xmin: {xmin_abs_frame} ymin: {ymin_abs_frame} xmax: {xmax_abs_frame} ymax: {ymax_abs_frame}\n"
                      f"OFFSETS: xoff: {self._x_offset} yoff: {self._y_offset}")
            bbox = BoundingBox.from_absolute(xmin=xmin_abs_frame, ymin=ymin_abs_frame, xmax=xmax_abs_frame, ymax=ymax_abs_frame,
                                             confidence=detection.confidence,
                                             image_height=self._FRAME_HEIGHT, image_width=self._FRAME_WIDTH,
                                             sequence_number=detections.getSequenceNum())
            self._bounding_boxes.append(bbox)

    def _increase_crop_count(self):
        self._crop_count += 1
        if self._crop_count >= self._TOTAL_CROP_COUNT:
            self._crop_count = 0

    def _send_results(self):
        if self._crop_count != self._TOTAL_CROP_COUNT - 1:  # counting crops from zero
            return
        log.debug(f"Sending results for sequence number: {self._sequence_number}")
        bboxes = self._bounding_boxes
        if len(bboxes) > 1:
            log.debug(f"BBoxes: {bboxes}")
            # make sure all detections are from the same frame
            if bboxes[0].getSequenceNum() != bboxes[-1].getSequenceNum():
                log.warning(
                    f"QR detections Sequence numbers are not the same: {bboxes[0].getSequenceNum()} != {bboxes[-1].getSequenceNum()}")
                # FindStart.enable()
                self._crop_count = len([bbox for bbox in bboxes if bbox.getSequenceNum() != bboxes[0].getSequenceNum])
                self._update_coord_offset()
                self._bounding_boxes.clear()
                return
        for i in range(len(bboxes)):
            bbox = bboxes[i]
            bbox.counter = i
        message = messages.QrBoundingBoxes(bounding_boxes=bboxes, sequence_number=self._sequence_number)
        self.send_message(message=message)

        self._bounding_boxes.clear()

    @staticmethod
    def perform_nms_on_bboxes(bounding_boxes: list[BoundingBox]) -> list[BoundingBox]:
        confidence_threshold = 0.5
        overlap_threshold = 0.01
        confidences = [bbox.confidence for bbox in bounding_boxes]
        nms_boxes = [bbox.as_nms_box() for bbox in bounding_boxes]
        indices = cv2.dnn.NMSBoxes(nms_boxes, confidences, confidence_threshold, overlap_threshold)
        bboxes_after_nms = []
        for index in indices:
            bboxes_after_nms.append(bounding_boxes[index])
        return bboxes_after_nms

    def _update_coord_offset(self):
        self._x_offset = int(self._OVERLAP_WIDTH * (self._crop_count // 3))
        self._y_offset = int(self._OVERLAP_HEIGHT * (self._crop_count % 3))
