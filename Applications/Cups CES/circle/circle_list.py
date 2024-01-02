import time
from typing import Callable, List

from .circle import Circle
from .circle_helper import is_active


class CircleList(List[Circle]):

    def _get_circles_filtered(self, condition: Callable[[Circle], bool]) -> 'CircleList':
        return CircleList(filter(condition, self))

    def get_active_circles(self) -> 'CircleList':
        return self._get_circles_filtered(is_active)

    def copy(self) -> 'CircleList':
        return CircleList(super().copy())

    def get_elapsed_times(self) -> List[float]:
        now = time.time()
        return [now - circle.appeared_at for circle in self]

    def get_circles_average_time(self) -> float:
        item_count = len(self)

        if item_count == 0:
            return 0.0

        current_time = time.time()
        active_circles_total_time = sum([current_time - circle.appeared_at for circle in self])

        return active_circles_total_time / item_count
