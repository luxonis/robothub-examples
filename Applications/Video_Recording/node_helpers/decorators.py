import logging as log
import math
import tracemalloc
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial, wraps
from time import perf_counter
from typing import Any, Callable


def measure_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = perf_counter()
        value = func(*args, **kwargs)
        end_time = perf_counter()
        run_time = end_time - start_time
        log.info(f"Execution of {func.__name__} took {run_time:.5f} seconds,")
        return value

    return wrapper


list_of_durations = defaultdict(list)
maximum_duration: dict[Any, float] = defaultdict(float)
minimum_duration: dict[Any, float] = defaultdict(lambda: 10_000_000)
last_report_at: dict[Any, float] = defaultdict(lambda: perf_counter())


def measure_average_performance(func: Callable[..., Any] = None, *, report_every_minutes: int = 5) -> Callable[..., Any]:
    """Report once every `report_every_minutes` minutes what the averages function duration is and what the max and min durations are."""
    if func is None:
        return partial(measure_average_performance, report_every_minutes=report_every_minutes)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        global list_of_durations, maximum_duration, minimum_duration, last_report_at
        start_time = perf_counter()
        value = func(*args, **kwargs)
        end_time = perf_counter()
        try:
            run_time = end_time - start_time
            if run_time > maximum_duration[func]:
                maximum_duration[func] = run_time
            if run_time < minimum_duration[func]:
                minimum_duration[func] = run_time
            list_of_durations[func].append(run_time)

            now = perf_counter()
            if now - last_report_at[func] > 1 * 60 * report_every_minutes and list_of_durations[func]:
                average_duration = sum(list_of_durations[func]) / len(list_of_durations[func])
                log.info("*" * 30)
                log.info(f"Performance stats for {func.__qualname__}:")
                log.info(f"Average duration: {average_duration * 1000:.2f} ms, Maximum duration: {maximum_duration[func] * 1000:.2f} ms, "
                         f"Minimal duration: {minimum_duration[func] * 1000:.2f} ms, Calls since last report: {len(list_of_durations[func])}")
                log.info("*" * 30)
                list_of_durations[func].clear()
                maximum_duration[func], minimum_duration[func] = 0, 10_000_000
                last_report_at[func] = perf_counter()
        except Exception:
            pass
        return value

    return wrapper


@dataclass
class FuncDetail:
    report_every_seconds: int
    last_call_at: float = field(default_factory=perf_counter)
    last_sum_at: float = field(default_factory=perf_counter)
    last_report_at: float = field(default_factory=perf_counter)
    call_frequency_memory: list = field(default_factory=list)
    sub_sums: list = field(default_factory=list)

    SUB_SUM_INTERVAL: int = 1

    def update_and_try_report(self, start_time: float, func_name: str) -> None:
        time_from_last_call = start_time - self.last_call_at
        self.last_call_at = start_time
        self.call_frequency_memory.append(time_from_last_call)

        if start_time - self.last_sum_at > self.SUB_SUM_INTERVAL:
            # in case there were no calls during sub interval(s)
            for _ in range((int(math.floor(start_time - self.last_sum_at)) // self.SUB_SUM_INTERVAL) - 1):
                self.sub_sums.append(0.)
            avg_cps = len(self.call_frequency_memory) / sum(self.call_frequency_memory)
            self.sub_sums.append(avg_cps)
            self.call_frequency_memory.clear()
            self.last_sum_at = perf_counter()

        if start_time - self.last_report_at > self.report_every_seconds and len(self.call_frequency_memory) == 0:
            avg_cps = sum(self.sub_sums) / len(self.sub_sums)
            min_cps = min(self.sub_sums)
            log.info("*" * 50)
            log.info(f"Calls per second stats for {func_name}:")
            log.info(f"Average calls per second (CPS): {avg_cps:.3f}, Minimal CPS: {min_cps:.3f}")
            log.info("*" * 50)
            self.sub_sums.clear()
            self.last_report_at = start_time


func_detail = defaultdict(lambda: FuncDetail(report_every_seconds=60 * 2))


def measure_call_frequency(func: Callable[..., Any]) -> Callable[..., Any]:
    """Measure how often a given function is called."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        global func_detail
        start_time = perf_counter()
        fd = func_detail[func]
        fd.update_and_try_report(start_time, func.__name__)

        value = func(*args, **kwargs)
        return value

    return wrapper


def with_sql_exception_handling(func: Callable[..., Any]) -> Callable[..., Any]:
    """Try sql operation command, catch exception and finally close the cursor and the connection."""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            log.error(f"Couldn't perform sql operation: {repr(e)}")
            return None

    return wrapper


def trace_memory(func: Callable[..., Any]) -> Callable[..., Any]:
    """Trace RAM usage."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracemalloc.start()
        value = func(*args, **kwargs)
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        log.info("*" * 50)
        log.info(f"TOP 10 RAM usage for {func.__name__}:")
        for stat in top_stats[:10]:
            log.info(stat)
        log.info("*" * 50)
        return value

    return wrapper
