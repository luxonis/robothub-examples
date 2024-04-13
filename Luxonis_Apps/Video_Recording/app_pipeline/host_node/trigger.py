
import logging as log
import threading
import time

import depthai as dai
import robothub as rh


class Trigger:

    def __init__(self, frequency_minutes: float | int, action: callable, device_stop_event: threading.Event):
        self._frequency_seconds = int(frequency_minutes * 60)
        self._action = action
        self._device_stop_event = device_stop_event
        self._thread = threading.Thread(target=self._run, name=self.__class__.__name__)
        log.info(f"Starting trigger {self.__class__.__name__} every {self._frequency_seconds}seconds")

    def run(self):
        self._thread.start()

    def stop(self):
        self._thread.join()

    def _run(self):
        rh.wait(self._frequency_seconds)
        while rh.app_is_running and not self._device_stop_event.is_set():
            try:
                self._action()
            except Exception as e:
                log.exception(f"Trigger action failed: {e=}\nTerminating trigger...")
                break
            rh.wait(self._frequency_seconds)
            time.sleep(1)
        log.info(f"Trigger {self.__class__.__name__} terminated")


def trigger_still_image(input_queue: dai.DataInputQueue):
    ctrl = dai.CameraControl()
    ctrl.setCaptureStill(True)
    log.info(f"Triggering still image")
    try:
        input_queue.send(ctrl)
    except RuntimeError as e:
        log.exception(f"Trigger action failed: {e=}\nWill retry next time...")


