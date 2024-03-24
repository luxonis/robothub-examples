import logging as log
import time


class IntervalTimer:
    """ IntervalTimer is used to check whether a certain time interval has already passed between events.
        Is used mainly to throttle frequency of certain messages, uploads, etc.
    """

    def __init__(self):
        self._event_timestamps = {}

    def update_timestamp(self, event):
        self._event_timestamps[event] = time.monotonic()

    def event_time_elapsed(self, event, seconds) -> bool:
        now = time.monotonic()
        last_ts = self._event_timestamps.get(event)
        log.debug(f'{event} {last_ts} {now} {seconds}')
        if last_ts is None:
            return True

        return (now - last_ts) >= seconds

    def events_followed(self, first_event, second_event) -> bool:
        first_ts = self._event_timestamps.get(first_event)
        second_ts = self._event_timestamps.get(second_event)
        log.debug(f'{first_event} {first_ts}, {second_event} {second_ts}')
        if (first_ts is None) or (second_ts is None):
            return False
        return first_ts <= second_ts

    def remove_event(self, event) -> None:
        self._event_timestamps.pop(event, None)
