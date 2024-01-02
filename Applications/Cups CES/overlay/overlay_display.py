import logging as log
from abc import ABC, abstractmethod


class OverlayDisplayer(ABC):

    def __init__(self):
        log.info(f"Initializing displayer {self.__class__.__name__}...")

    @abstractmethod
    def display_circles(self, image, circles) -> None:
        pass

    @abstractmethod
    def display_info(self, image, text) -> None:
        pass
