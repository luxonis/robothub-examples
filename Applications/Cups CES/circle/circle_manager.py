import cv2
import logging as log
import time
import numpy as np
from typing import List, Tuple

from circle import circle_helper
from circle.circle import Circle
from circle.circle_list import CircleList
from circle.circle_processor import CircleProcessor
from depthai_sdk import FramePacket
from overlay.overlay_manager import OverlayManager


class CircleManager:

    def __init__(self, overlay_manager: OverlayManager):
        self.circle_list: CircleList = CircleList()
        self._disappeared_circles_duration: List[int] = []
        self._circle_processor: CircleProcessor = CircleProcessor()
        self.overlay_manager: OverlayManager = overlay_manager
        self._refresh_rate_seconds = 1.
        self._last_refresh_time = time.monotonic()

    def refresh_circles(self, image_frame: np.ndarray):
        now = time.monotonic()

        if now - self._last_refresh_time >= self._refresh_rate_seconds:
            self._last_refresh_time = now
            # Process image frame and update circles
            self.update_circles(self._circle_processor.process_circles(image_frame))

            log.debug(f"Disappeared circles: {self._disappeared_circles_duration}")

        # Refresh overlay
        self.overlay_manager.refresh_overlay(
            image_frame,
            self.circle_list.get_active_circles(),
            self._disappeared_circles_duration.copy()
        )

    def update_circles(self, new_circles: List[Tuple[int, int, int]]) -> None:
        circles = self.circle_list.copy()

        [
            log.debug(
                f"Circle {circle.circle_id} - "
                f"at {circle.center_coordinates} - "
                f"radius {circle.radius} - "
                f"time {circle_helper.format_seconds_into_timer(time.time() - circle.appeared_at)} - "
                f"history {circle.history.count(True)}x"
            )
            for circle in circles
        ]

        active_circles = []

        for new_circle in new_circles:
            circle_found = False

            # Check if new circle is similar to any existing circle
            for i, existing_circle in enumerate(circles):
                same_circle = circle_helper.are_circles_similar(existing_circle, new_circle)

                if same_circle:
                    # Existing circle found
                    updated_circle = existing_circle.update(*new_circle)
                    active_circles.append(updated_circle)

                    if circle_helper.is_active(updated_circle) and not updated_circle.active_once:
                        # If circle is active, and it wasn't active before, we need to set it as active once
                        log.debug(f"Circle {updated_circle.circle_id} reached active state.")
                        updated_circle.set_active_once()

                    # Remove outdated circle from circles
                    circles.pop(i)

                    circle_found = True
                    break

            if not circle_found:
                # New circle found
                active_circles.append(Circle(*new_circle))
                log.debug(f"New circle {active_circles[-1].circle_id} was added.")

        # Get not active circles by subtracting active circles from all circles
        not_active_circles = [circle for circle in circles if circle not in active_circles]

        # Iterate over not active circles and check if they should be removed due to inactivity
        for i, circle in enumerate(not_active_circles):
            circle.not_seen()

            if circle_helper.is_inactive(circle):
                not_active_circles.pop(i)

                if circle.active_once:
                    # If circle reached active state at least once, we can append it to disappeared circles
                    self._disappeared_circles_duration.append(time.time() - circle.appeared_at)
                    log.debug(f"Circle {circle.circle_id} was removed due to inactivity.")

        # Merge active and not active circles
        self.circle_list = CircleList(active_circles + not_active_circles)
