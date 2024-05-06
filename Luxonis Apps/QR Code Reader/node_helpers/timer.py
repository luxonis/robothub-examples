from time import monotonic


class Timer:

    def __init__(self):
        self.start_time = None

    def reset(self):
        self.start_time = monotonic()

    def elapsed_seconds(self) -> float:
        return monotonic() - self.start_time

    def has_elapsed(self, time_in_seconds: float) -> bool:
        return self.elapsed_seconds() >= time_in_seconds
