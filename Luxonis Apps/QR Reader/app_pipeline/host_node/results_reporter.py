import logging as log
from collections import deque
from typing import Callable

import cv2
import numpy as np
import robothub as rh

from app_pipeline import host_node, messages
from node_helpers import Timer

__all__ = ["ResultsReporter"]


class ResultsReporter(host_node.BaseNode):
    NOT_SEED_THRESHOLD = 10

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)

        self._rh_report_buffer = deque(maxlen=4)
        self._last_rh_report_sent = Timer()
        self._last_rh_report_sent.reset()
        self._qr_code_memory = {}  # label -> not seen for x frames

    def __callback(self, frames_and_detections: messages.FramesWithDetections):
        qr_detections = frames_and_detections.qr_bboxes.bounding_boxes
        new_qr_codes = {}
        existing_qr_codes = {}
        for qr_code in qr_detections:
            if qr_code.label and qr_code.label not in self._qr_code_memory:
                self._qr_code_memory[qr_code.label] = 0
                new_qr_codes[qr_code.label] = qr_code
            else:
                existing_qr_codes[qr_code.label] = qr_code

        if new_qr_codes:
            log.info(f"New QR codes found: {new_qr_codes.keys()}")
            context_image = frames_and_detections.high_res_rgb.frame
            qr_boxes = messages.QrBoundingBoxes(bounding_boxes=list(new_qr_codes.values()), sequence_number=frames_and_detections.getSequenceNum())
            for bbox in qr_boxes.bounding_boxes:
                xmin, ymin, xmax, ymax = bbox.transform(width=rh.CONFIGURATION["merged_image_width"], height=rh.CONFIGURATION["merged_image_height"])
                context_image = cv2.rectangle(context_image, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 0, 255), 2)
                # write label on the frame
                label = f"{bbox.label}, {bbox.confidence:.3f}"
                cv2.putText(context_image, label, (int(xmin), int(ymin - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)

            rh_report = messages.RhReport(context_image=context_image, qr_bboxes=qr_boxes,
                                          sequence_number=frames_and_detections.getSequenceNum())
            if len(self._rh_report_buffer) < self._rh_report_buffer.maxlen:
                self._rh_report_buffer.append(rh_report)
            else:
                log.warning(f"Too many reports in buffer, dropping {rh_report.getSequenceNum()=}")

        if self._last_rh_report_sent.has_elapsed(time_in_seconds=35) and len(self._rh_report_buffer) > 0:
            self._last_rh_report_sent.reset()
            rh_report: messages.RhReport = self._rh_report_buffer.popleft()
            log.info(f"Sending QR code report with {len(rh_report.qr_bboxes.bounding_boxes)} QR codes")
            rh.send_image_event(image=rh_report.context_image,
                                title="QR CODE REPORT",
                                device_id=rh.DEVICE_MXID,
                                tags=["qr_code_report"],
                                encode=True,
                                mjpeg_quality=60)

        for qr_code_label in list(self._qr_code_memory.keys()):
            # when seen, reset counter to zero, because it means for how long ar label was not spotted
            if qr_code_label in existing_qr_codes:
                self._qr_code_memory[qr_code_label] = 0
            # not in new and not in existing, increment counter
            elif qr_code_label not in new_qr_codes:
                self._qr_code_memory[qr_code_label] += 1
                if self._qr_code_memory[qr_code_label] >= self.NOT_SEED_THRESHOLD:
                    log.info(f"QR code {qr_code_label} not seen for {self._qr_code_memory[qr_code_label]} frames, removing from memory.")
                    self._qr_code_memory.pop(qr_code_label)
