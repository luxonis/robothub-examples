import time
import uuid
from collections import deque
from typing import Tuple, Deque

from config import CIRCLE_HISTORY_LENGTH


class Circle:

    def __init__(self, x: int, y: int, r: int):
        self._x: int = x
        self._y: int = y
        self._r: int = r
        self._circle_id: str = str(uuid.uuid4())
        self._appeared_at: float = time.time()
        self._history: Deque[bool] = deque(maxlen=CIRCLE_HISTORY_LENGTH)
        self._active_once: bool = False

    @property
    def circle_id(self) -> str:
        return self._circle_id

    @property
    def appeared_at(self) -> float:
        return self._appeared_at

    @property
    def history(self) -> Deque[bool]:
        return self._history

    @property
    def active_once(self) -> bool:
        return self._active_once

    @property
    def center_coordinates(self) -> Tuple[int, int]:
        return self._x, self._y

    @property
    def radius(self) -> int:
        return self._r

    def seen(self) -> None:
        self._history.append(True)

    def not_seen(self) -> None:
        self._history.append(False)

    def set_active_once(self) -> None:
        self._active_once = True

    def update(self, x: int, y: int, r: int) -> 'Circle':
        self._x = x
        self._y = y
        self._r = r
        self.seen()
        return self
