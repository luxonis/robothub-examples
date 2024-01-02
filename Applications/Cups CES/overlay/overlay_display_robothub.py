import logging as log
import time
from typing import Optional
import numpy as np
from robothub import LiveView

from config import LOGGING_LEVEL
from circle.circle_helper import format_seconds_into_timer
from circle.circle_list import CircleList
from overlay.overlay_display import OverlayDisplayer


class OverlayDisplayerRobothub(OverlayDisplayer):

    def __init__(self):
        super().__init__()
        self.live_view: Optional[LiveView] = None

    def set_live_view(self, live_view: LiveView) -> None:
        self.live_view = live_view

    def display_circles(self, image: np.ndarray, circles: CircleList) -> None:
        if not self.live_view:
            log.error('You need to set the LiveView first.')
            return

        for circle in circles:
            (x, y), r = circle.center_coordinates, circle.radius

            self.live_view.add_rectangle(
                (int(x - r), int(y - r), int(x + r), int(y + r)),
                f"{circle.circle_id + ' ' if LOGGING_LEVEL == 0 else ''}"
                f"{format_seconds_into_timer(time.time() - circle.appeared_at)}"
            )

    def display_info(self, image: np.ndarray, text: str) -> None:
        if not self.live_view:
            log.error('You need to set the LiveView first.')
            return

        x, y0 = (50, 50)
        line_height = 30

        for i, line in enumerate(text.split('\n')):
            y = y0 + i * line_height
            self.live_view.add_text(line, (x, y))
