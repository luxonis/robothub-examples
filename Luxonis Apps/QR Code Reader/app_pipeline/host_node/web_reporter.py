import logging as log
from collections import deque

import cv2
from datetime import datetime
import requests

from app_pipeline import host_node, messages

__all__ = ["WebReporter"]

SERVER_URL = "http://127.0.0.1:5000/webhook"  # TODO This is only for tests


class WebReporter(host_node.BaseNode):
    NOT_SEEN_THRESHOLD = 10
    ELAPSED_TIME_THRESHOLD = 10
    MAX_REPORT_BUFFER_LEN = 4

    def __init__(self, input_node: host_node.BaseNode):
        super().__init__()
        input_node.set_callback(callback=self.__callback)

        self._web_report_buffer = deque(maxlen=self.MAX_REPORT_BUFFER_LEN)
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
            log.info(f"[WebReporter] New QR codes found: {new_qr_codes.keys()}")
            qr_boxes = messages.QrBoundingBoxes(bounding_boxes=list(new_qr_codes.values()),
                                                sequence_number=frames_and_detections.getSequenceNum())
            for bbox in qr_boxes.bounding_boxes:
                web_report = messages.WebReport(crop_image=bbox.crop.getCvFrame(), label=bbox.label,
                                                code_format=bbox.code_format, timestamp=datetime.now(),
                                                sequence_number=frames_and_detections.getSequenceNum())
                if len(self._web_report_buffer) < self._web_report_buffer.maxlen:
                    self._web_report_buffer.append(web_report)
                else:
                    log.warning(f"[WebReporter] Too many reports in buffer, dropping {web_report.getSequenceNum()}")

        if len(self._web_report_buffer) > 0:
            web_report: messages.WebReport = self._web_report_buffer.popleft()
            log.info(f"[WebReporter] Sending QR code report with label {web_report.label}")
            self.__send_report(web_report)

        for qr_code_label in list(self._qr_code_memory.keys()):
            # when seen, reset counter to zero, because it means for how long ar label was not spotted
            if qr_code_label in existing_qr_codes:
                self._qr_code_memory[qr_code_label] = 0
            # not in new and not in existing, increment counter
            elif qr_code_label not in new_qr_codes:
                self._qr_code_memory[qr_code_label] += 1
                if self._qr_code_memory[qr_code_label] >= self.NOT_SEEN_THRESHOLD:
                    log.info(f"[WebReporter] QR code {qr_code_label} not seen for {self._qr_code_memory[qr_code_label]} frames, removing from memory.")
                    self._qr_code_memory.pop(qr_code_label)

    @staticmethod
    def __send_report(report: messages.WebReport) -> None:
        """Send the report on the customer URL."""
        try:
            response = requests.post(SERVER_URL, json=report.to_dict())
            if response.status_code == 200:
                log.info("[WebReporter] Data was successfully received!")
            else:
                log.error(f"[WebReporter] {response.status_code} - {response.text}")
        except Exception as e:
            log.error(f"[WebReporter] {e}")
