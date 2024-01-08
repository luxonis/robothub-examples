import numpy as np
from typing import List, Optional

import config
from circle.circle_helper import format_seconds_into_timer
from circle.circle_list import CircleList
from overlay.overlay_display import OverlayDisplayer


class OverlayManager:

    def __init__(self, displayer: OverlayDisplayer):
        self._image: Optional[np.ndarray] = None
        self._displayer: Optional[OverlayDisplayer] = displayer

    def refresh_overlay(self, image: np.ndarray, thermal_frame, colored_thermal_frame,
                        circles: CircleList, disappeared_circles_duration: List[int]) -> None:
        self._image = image

        active_circles_count = len(circles)
        active_circles_average_time = round(circles.get_active_circles().get_circles_average_time())
        active_circles_elapsed_times = circles.get_elapsed_times()

        disappeared_circles_count = len(disappeared_circles_duration)

        total_circles_count = active_circles_count + disappeared_circles_count
        total_elapsed_time_average = round(
            0
            if total_circles_count == 0
            else sum(active_circles_elapsed_times + disappeared_circles_duration) / total_circles_count
        )

        self._displayer.display_circles(self._image, circles)
        self._displayer.display_thermal(self._image, thermal_frame, colored_thermal_frame, circles)
        self._displayer.display_info(
            self._image,
            f"{config.VISIBLE_CIRCLES_STRING.format(active_circles_count)}\n"
            f"{config.REMOVED_CIRCLES_STRING.format(disappeared_circles_count)}\n"
            f"{config.AVERAGE_TIME_VISIBLE_CIRCLES_STRING.format(format_seconds_into_timer(active_circles_average_time))}\n"
            f"{config.AVERAGE_TIME_ALL_CIRCLES_STRING.format(format_seconds_into_timer(total_elapsed_time_average))}"
        )
