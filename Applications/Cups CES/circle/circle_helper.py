import logging as log
import numpy as np
from typing import Tuple

from .circle import Circle
from config import CIRCLE_HISTORY_LENGTH, CIRCLE_PRESENCE_THRESHOLD, CIRCLE_RADIUS_TOLERANCE, CIRCLE_DISTANCE_TOLERANCE


def is_inactive(circle: Circle) -> bool:
    circle_inactive = circle.history and circle.history.count(False) > CIRCLE_HISTORY_LENGTH * CIRCLE_PRESENCE_THRESHOLD

    if circle_inactive:
        log.debug(f"Circle recognized as inactive: {circle.circle_id}")
        log.debug(f"Circle {circle.circle_id} inactive, not seen {circle.history.count(False)}x, "
                  f"seen {circle.history.count(True)}x")
        log.debug(f"Condition values: "
                  f"{circle.history.count(False)=} > {CIRCLE_HISTORY_LENGTH=} * {CIRCLE_PRESENCE_THRESHOLD=}")

    return circle_inactive


def is_active(circle: Circle) -> bool:
    return circle.history and circle.history.count(True) >= CIRCLE_HISTORY_LENGTH * CIRCLE_PRESENCE_THRESHOLD


def are_circles_similar(circle1: Circle, circle2: Tuple[int, int, int]) -> bool:
    (x1, y1), r1 = circle1.center_coordinates, circle1.radius
    x2, y2, r2 = circle2

    radius_tolerance_coefficient = r1 * CIRCLE_RADIUS_TOLERANCE
    distance_of_circle_centers = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    if not (abs(r1 - r2) < radius_tolerance_coefficient and distance_of_circle_centers < CIRCLE_DISTANCE_TOLERANCE):
        log.debug(f"Circles are not similar, see below:")
        log.debug(f"Circle {circle1.circle_id} with center ({x1}, {y2}) and radius {r1}")
        log.debug(f"New circle with center ({x2}, {y2}) and radius {r2}")
        log.debug(f"{abs(r1 - r2)=} < {radius_tolerance_coefficient=}")
        log.debug(f"{distance_of_circle_centers=} < {CIRCLE_DISTANCE_TOLERANCE=}")

    return abs(r1 - r2) < radius_tolerance_coefficient and distance_of_circle_centers < CIRCLE_DISTANCE_TOLERANCE


def format_seconds_into_timer(seconds: float) -> str:
    elapsed_seconds = seconds
    minutes, seconds = divmod(elapsed_seconds, 60)
    return "{:02}:{:02}".format(int(minutes), int(seconds))
