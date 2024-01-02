import cv2 as cv
import time
import numpy as np

import config
from circle.circle import Circle
from circle.circle_helper import format_seconds_into_timer
from circle.circle_list import CircleList
from overlay.overlay_display import OverlayDisplayer


class OverlayDisplayerStandalone(OverlayDisplayer):

    def display_circles(self, image: np.ndarray, circles: CircleList) -> None:
        [self.process_circle(image, circle) for circle in circles]

    def display_info(self, image, text) -> None:
        font_scale = 1
        thickness = 2

        text_size, _ = cv.getTextSize(text, config.OPEN_CV_FONT, font_scale, thickness)
        line_height = text_size[1] + 10
        x, y0 = (0, text_size[1])

        for i, line in enumerate(text.split('\n')):
            y = y0 + i * line_height
            cv.putText(image, line, (x, y), config.OPEN_CV_FONT, font_scale, (255, 255, 255), thickness, cv.LINE_AA)

    def place_text_in_circle(self, x: int, y: int, text: str, image: np.ndarray) -> None:
        font_scale = 0.7
        font_thickness = 1

        text_size = cv.getTextSize(text, config.OPEN_CV_FONT, font_scale, font_thickness)[0]
        text_position = (int(x - text_size[0] / 2), int(y + text_size[1] / 2))

        cv.putText(image, text, text_position, config.OPEN_CV_FONT,
                   font_scale, (255, 255, 255), font_thickness, cv.LINE_AA)

    def process_circle(self, image: np.ndarray, circle: Circle) -> None:
        (x, y), r = circle.center_coordinates, circle.radius
        cv.circle(image, (x, y), r, (0, 255, 0), 4)

        text = (f"{circle.circle_id + ' ' if config.LOGGING_LEVEL == 0 else ''}"
                f"{format_seconds_into_timer(time.time() - circle.appeared_at)}")

        self.place_text_in_circle(x, y, text, image)
