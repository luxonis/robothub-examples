import logging as log
import threading
import time

import depthai as dai
import robothub as rh
from app_pipeline import host_node


class Bridge(host_node.BaseNode):
    __bridges: list = []

    def __init__(self, device: dai.Device, out_name: str, blocking: bool = True, queue_size: int = 2):
        super().__init__()
        self._out_queue = device.getOutputQueue(name=out_name, maxSize=queue_size, blocking=blocking)
        self._get_depthai_message = self._out_queue.get if blocking else self._out_queue.tryGet
        self.__bridges.append(self)

    @classmethod
    def run(cls, device_stop_event: threading.Event):
        while rh.app_is_running() and not device_stop_event.is_set():
            for bridge in cls.__bridges:
                try:
                    bridge._poll()
                except RuntimeError as e:
                    log.error(f'Bridge poll failed with error: {e}')
                    device_stop_event.set()
                    cls.__bridges.clear()
                    break
            time.sleep(0.01)

    def _poll(self):
        message = self._get_depthai_message()
        if message is not None:
            self.send_message(message)
