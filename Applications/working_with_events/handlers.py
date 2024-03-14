import time
import logging as log
from threading import Event

import robothub as rh
import depthai as dai


class EventHandler:
    def __init__(self):
        self.last_upload = None
        self.take_picture_signal = Event()
        rh.COMMUNICATOR.on_frontend(notification=self.on_fe_notification)

    def on_fe_notification(self, session_id, unique_key, payload):
        if unique_key == 'take_picture':
            print("Received take picture notification from FE")
            self.take_picture_signal.set()

    def check_interval(self) -> bool:
        current_time = time.time()
        if not self.last_upload or current_time - self.last_upload >= rh.CONFIGURATION["event_upload_interval"]:
            self.last_upload = current_time
            return True
        return False

    def send_spaced_img_event_on_detection(self, detections: dai.ImgDetections, rgb_mjpeg_frame: dai.ImgFrame,
                                           device_id: str):
        if detections.detections and self.check_interval():
            rh.events.send_image_event(image=rgb_mjpeg_frame.getFrame(), title="Person detected",
                                       device_id=device_id)

    def send_event_on_fe_notification(self, rgb_mjpeg_frame: dai.ImgFrame, device_id: str):
        if self.take_picture_signal.is_set():
            self.take_picture_signal.clear()
            log.info(f"Sending Event...")
            rh.events.send_image_event(image=rgb_mjpeg_frame.getFrame(), title="Front-end event image",
                                       device_id=device_id)