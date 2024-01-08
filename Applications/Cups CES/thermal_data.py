import cv2
import numpy as np
import time


class ThermalData:

    def __init__(self):
        self._thermal_frame = None
        self._colored_frame = None
        self.last_update = time.monotonic()
        self._update_frequency = 2

    @property
    def thermal_frame(self):
        return self._thermal_frame

    @property
    def colored_frame(self):
        return self._colored_frame

    def update_frame(self, thermal_frame: np.ndarray):
        now = time.monotonic()
        if now - self.last_update > self._update_frequency:
            thermal_frame = cv2.resize(thermal_frame, (1920, 1080))
            color_mapped_image = cv2.applyColorMap(thermal_frame, cv2.COLORMAP_JET)

            self._colored_frame = color_mapped_image
            self._thermal_frame = thermal_frame
            self.last_update = now


class MockPacket:

    def __init__(self, frame):
        self.frame = frame
    def getCvFrame(self):
        return self.frame


class ThermalMock:
    last_update = time.monotonic()
    mean = 28
    std_dev = 20

    def tryGet(self):
        now = time.monotonic()
        if now - self.last_update > 1:
            self.last_update = now
            random_image = np.random.normal(self.mean, self.std_dev, (480, 640)).astype(np.uint8)
            random_image = np.clip(random_image, 0, 255)
            return MockPacket(random_image)

