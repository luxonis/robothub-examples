import logging as log
import time

from app_pipeline import host_node
from app_pipeline.messages import Message


class RegularEvent(host_node.BaseNode):

    def __init__(self, input_node: host_node.BaseNode, name: str, frequency_seconds: int = 60):
        super().__init__()
        input_node.set_callback(callback=self.__callback)

        self.name = name
        self.frequency_seconds = frequency_seconds
        self._last_event_sent = time.monotonic()

    def __callback(self, message: Message) -> None:
        now = time.monotonic()
        if now - self._last_event_sent > self.frequency_seconds:
            log.info(f"Sending regular event {self.name}, frequency: {self.frequency_seconds}s")
            self.send_message(message=message)
            self._last_event_sent = now
